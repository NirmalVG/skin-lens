from dotenv import load_dotenv
import os
load_dotenv()
from pydantic import BaseModel
from sqlalchemy import or_

from fastapi import FastAPI, Depends, UploadFile, File, Form, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from database import get_db, Base, engine
from auth import create_access_token, get_current_user
from ocr_service import extract_ingredients_from_image
from models import Ingredient, SafetyRating, User, QuizResult
import requests

class QuizRequest(BaseModel):
    skin_type: str
    sensitivities: str = "none"

# 1. INITIALIZE THE APP
app = FastAPI(title="Skin Lens API")

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")

# Auto-create database tables on startup
@app.on_event("startup")
def on_startup():
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables verified / created.")
    except Exception as e:
        print(f"⚠️  Could not auto-create tables (DB may be unreachable): {e}")

# 2. CORS
origins = [
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:5175",
    "http://localhost:5176",
    "https://skin-lens.netlify.app"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Authorization"],
)

# Add COOP header for Google OAuth popup communication
@app.middleware("http")
async def add_coop_header(request, call_next):
    response = await call_next(request)
    response.headers["Cross-Origin-Opener-Policy"] = "same-origin-allow-popups"
    return response


# Helper: build a consistent user dict for responses
def _user_dict(user: User) -> dict:
    return {
        "id":        user.id,
        "name":      user.name      or "",
        "email":     user.email     or "",
        "picture":   user.profile_picture or "",
        "skin_type": user.skin_type or "Normal",  # ← add fallback
    }


# ==========================================
# ROUTE 1: SEARCH & PAGINATION
# ==========================================
@app.get("/api/ingredients/search")
def search_ingredients(
    query: str = "",
    risk: str = "",
    page: int = 1,
    db: Session = Depends(get_db)
):
    limit = 12
    offset = (page - 1) * limit

    qs = db.query(Ingredient)

    if query:
        qs = qs.filter(Ingredient.name.ilike(f"%{query}%"))

    if risk and risk.strip():
        rating_map = {r.value: r for r in SafetyRating}
        matched_enum = rating_map.get(risk)
        if matched_enum:
            qs = qs.filter(Ingredient.safety_rating == matched_enum)

    total = qs.count()
    items = qs.offset(offset).limit(limit).all()

    return {
        "items": [{
            "id": i.id,
            "name": i.name,
            "safety_rating": i.safety_rating.value,
            "description": i.description,
            "compatible_skin_types": i.compatible_skin_types
        } for i in items],
        "total": total,
        "page": page,
        "pages": (total // limit) + (1 if total % limit > 0 else 0)
    }

# ==========================================
# ROUTE 2: THE "LENS" (OCR & AI FALLBACK)
# ==========================================
@app.post("/api/analyze/image")
async def analyze_label(file: UploadFile = File(...), db: Session = Depends(get_db)):
    bytes_data = await file.read()
    ingredients = extract_ingredients_from_image(bytes_data)

    if not ingredients:
        raise HTTPException(status_code=422, detail="No ingredients found in image")

    results = []

    for ing in ingredients:
        matched = db.query(Ingredient).filter(
            Ingredient.name.ilike(f"%{ing['name']}%")
        ).first()

        if matched:
            results.append({
                "name": matched.name,
                "safety_rating": matched.safety_rating.value,
                "description": matched.description,
                "compatible_skin_types": matched.compatible_skin_types,
                "source": "database"
            })
        else:
            results.append({
                "name": ing["name"],
                "safety_rating": ing["safety_rating"],
                "description": ing["description"],
                "compatible_skin_types": ing["compatible_skin_types"],
                "source": ing.get("source", "ai")  
            })

    avoid_count = sum(1 for r in results if r["safety_rating"] == "Avoid")
    irritant_count = sum(1 for r in results if r["safety_rating"] == "Irritant")
    moderate_count = sum(1 for r in results if r["safety_rating"] == "Moderate")
    safe_count = sum(1 for r in results if r["safety_rating"] == "Safe")

    return {
        "ingredients": results,
        "extracted_raw_count": len(results),
        "summary": {
            "avoid": avoid_count,
            "irritant": irritant_count,
            "moderate": moderate_count,
            "safe": safe_count,
            "unknown": 0
        }
    }

# ==========================================
# ROUTE 3: QUIZ RECOMMENDATIONS
# ==========================================
# ==========================================
# ROUTE 3: QUIZ RECOMMENDATIONS
# ==========================================
@app.post("/api/quiz/recommendations")
def get_recommendations(
    data: QuizRequest, # <-- Now expects JSON!
    db: Session = Depends(get_db)
):
    qs = db.query(Ingredient).filter(Ingredient.safety_rating == SafetyRating.SAFE)
    qs = qs.filter(or_(
        Ingredient.compatible_skin_types.ilike(f"%{data.skin_type}%"),
        Ingredient.compatible_skin_types.ilike("%All%")
    ))
    top_ingredients = qs.limit(5).all()

    return {
        "skin_type": data.skin_type,
        "recommended_ingredients": [{
            "name": i.name,
            "description": i.description
        } for i in top_ingredients]
    }

# ==========================================
# ROUTE 4: HEALTH CHECK
# ==========================================
@app.get("/health")
def health():
    return {"status": "ok"}



# ==========================================
# ROUTE 8: PROTECTED — GET CURRENT USER
# ==========================================
@app.get("/api/auth/me")
def get_me(current_user: User = Depends(get_current_user)):
    """Return the currently authenticated user's info. Requires a valid JWT."""
    return _user_dict(current_user)


# ==========================================
# ROUTE 9: GOOGLE OAUTH
# ==========================================
@app.post("/api/auth/google")
async def google_auth(request: Request, db: Session = Depends(get_db)):
    body  = await request.json()
    token = body.get("token")

    if not token:
        raise HTTPException(status_code=400, detail="Token missing")

    # Call Google userinfo endpoint
    try:
        response = requests.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {token}"}
        )
        info = response.json() # ← shows real error in terminal
    except Exception as e:
        raise HTTPException(status_code=400, detail="Could not reach Google")

    # Check for errors separately
    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="Invalid Google token")

    email     = info.get("email")
    name      = info.get("name")
    picture   = info.get("picture")
    google_id = info.get("sub")

    if not email:
        raise HTTPException(status_code=400, detail="Could not get email from Google")

    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            user = User(
                name=name,
                email=email,
                google_id=google_id,
                profile_picture=picture
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        else:
            if not user.google_id:
                user.google_id = google_id
            if not user.profile_picture:
                user.profile_picture = picture
            db.commit()
            db.refresh(user)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Database error")

    jwt_token = create_access_token({"sub": user.email})
    return {
        "access_token": jwt_token,
        "token_type":   "bearer",
        "user":         _user_dict(user)
    }


# ==========================================
# ROUTE 10: ADMIN — STATS
# ==========================================
@app.get("/api/admin/stats")
def admin_stats(db: Session = Depends(get_db)):
    total = db.query(Ingredient).count()
    safe = db.query(Ingredient).filter(Ingredient.safety_rating == SafetyRating.SAFE).count()
    moderate = db.query(Ingredient).filter(Ingredient.safety_rating == SafetyRating.MODERATE).count()
    irritant = db.query(Ingredient).filter(Ingredient.safety_rating == SafetyRating.IRRITANT).count()
    avoid = db.query(Ingredient).filter(Ingredient.safety_rating == SafetyRating.AVOID).count()
    users = db.query(User).count()  # ← add this
    return {
        "total": total, "safe": safe, "moderate": moderate,
        "irritant": irritant, "avoid": avoid,
        "total_users": users  # ← add this
    }


# ==========================================
# ROUTE 11: ADMIN — ADD INGREDIENT
# ==========================================
@app.post("/api/admin/ingredient")
def add_ingredient(
    name: str = Form(...),
    safety_rating: str = Form(...),
    description: str = Form(""),
    compatible_skin_types: str = Form("All"),
    db: Session = Depends(get_db)
):
    rating_map = {r.value: r for r in SafetyRating}
    rating = rating_map.get(safety_rating)
    if not rating:
        raise HTTPException(status_code=400, detail="Invalid safety rating")

    existing = db.query(Ingredient).filter(Ingredient.name == name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Ingredient already exists")

    new_ing = Ingredient(
        name=name,
        safety_rating=rating,
        description=description,
        compatible_skin_types=compatible_skin_types
    )
    db.add(new_ing)
    db.commit()
    db.refresh(new_ing)
    return {"message": "Ingredient added", "id": new_ing.id}


# ==========================================
# ROUTE 12: ADMIN — UPDATE INGREDIENT
# ==========================================
@app.put("/api/admin/ingredient/{ingredient_id}")
async def update_ingredient(
    ingredient_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    ing = db.query(Ingredient).filter(Ingredient.id == ingredient_id).first()
    if not ing:
        raise HTTPException(status_code=404, detail="Ingredient not found")

    body = await request.json()

    if "name" in body:
        ing.name = body["name"]
    if "safety_rating" in body:
        rating_map = {r.value: r for r in SafetyRating}
        rating = rating_map.get(body["safety_rating"])
        if rating:
            ing.safety_rating = rating
    if "description" in body:
        ing.description = body["description"]
    if "compatible_skin_types" in body:
        ing.compatible_skin_types = body["compatible_skin_types"]

    db.commit()
    db.refresh(ing)
    return {"message": "Ingredient updated"}


# ==========================================
# ROUTE 13: ADMIN — DELETE INGREDIENT
# ==========================================
@app.delete("/api/admin/ingredient/{ingredient_id}")
def delete_ingredient(ingredient_id: int, db: Session = Depends(get_db)):
    ing = db.query(Ingredient).filter(Ingredient.id == ingredient_id).first()
    if not ing:
        raise HTTPException(status_code=404, detail="Ingredient not found")
    db.delete(ing)
    db.commit()
    return {"message": "Ingredient deleted"}

# ==========================================
# SAVE QUIZ RESULT
# ==========================================
@app.post("/api/quiz/save")
def save_quiz_result(
    data: QuizRequest, # <-- This tells FastAPI to read the incoming JSON!
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Delete old result for this user if exists
    old = db.query(QuizResult).filter(
        QuizResult.user_id == current_user.id
    ).first()
    
    if old:
        db.delete(old)

    # Create the new result using the data from the JSON request
    result = QuizResult(
        user_id=current_user.id,
        skin_type=data.skin_type,
        sensitivities=data.sensitivities,
    )
    
    db.add(result)
    db.commit()
    db.refresh(result)
    
    return {"message": "Quiz result saved", "skin_type": data.skin_type}


# ==========================================
# GET PREVIOUS QUIZ RESULT
# ==========================================
@app.get("/api/quiz/my-result")
def get_my_quiz_result(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = db.query(QuizResult).filter(
        QuizResult.user_id == current_user.id
    ).first()

    if not result:
        return {"has_result": False}

    # Get recommendations for saved skin type
    qs = db.query(Ingredient).filter(
        Ingredient.safety_rating == SafetyRating.SAFE
    ).filter(or_(
        Ingredient.compatible_skin_types.ilike(f"%{result.skin_type}%"),
        Ingredient.compatible_skin_types.ilike("%All%")
    )).limit(5).all()

    return {
        "has_result":   True,
        "skin_type":    result.skin_type,
        "taken_on":     result.created_at.strftime("%B %d, %Y"),
        "recommended_ingredients": [
            {"name": i.name, "description": i.description}
            for i in qs
        ]
    }

@app.get("/api/admin/users")
def get_all_users(db: Session = Depends(get_db)):
    users = db.query(User).order_by(User.created_at.desc()).all()
    return [_user_dict(u) for u in users]   