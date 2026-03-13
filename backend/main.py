from dotenv import load_dotenv
import os
load_dotenv()

from fastapi import FastAPI, Depends, UploadFile, File, Form, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc
from typing import List

from database import get_db, Base, engine
from models import Ingredient, SafetyRating, User
from schemas import UserCreate, UserLogin, Token
from auth import hash_password, verify_password, create_access_token, get_current_user
from ocr_service import extract_ingredients_from_image
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

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


# Helper: build a consistent user dict for responses
def _user_dict(user: User) -> dict:
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "picture": user.profile_picture,
        "skin_type": user.skin_type,
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
                "source": "ai"
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
@app.post("/api/quiz/recommendations")
def get_recommendations(
    skin_type: str = Form(...),
    sensitivities: str = Form(...),
    db: Session = Depends(get_db)
):
    qs = db.query(Ingredient).filter(Ingredient.safety_rating == SafetyRating.SAFE)
    qs = qs.filter(or_(
        Ingredient.compatible_skin_types.ilike(f"%{skin_type}%"),
        Ingredient.compatible_skin_types.ilike("%All%")
    ))
    top_ingredients = qs.limit(5).all()

    return {
        "skin_type": skin_type,
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
# ROUTE 5: AUTHENTICATION — REGISTER (Form Data)
# ==========================================
@app.post("/api/auth/register")
def register(
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    skin_type: str = Form("Normal"),
    db: Session = Depends(get_db)
):
    """
    Register a new user via form data.
    Used by the Register page which sends FormData.
    """
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = User(
        name=name,
        email=email,
        hashed_password=hash_password(password),
        skin_type=skin_type,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    token = create_access_token({"sub": new_user.email})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": _user_dict(new_user)
    }


# ==========================================
# ROUTE 6: AUTHENTICATION — SIGNUP (JSON Body)
# ==========================================
@app.post("/api/auth/signup", response_model=Token)
def signup(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user via JSON body.
    Kept for backwards compatibility with tests.
    """
    existing = db.query(User).filter(User.email == user_data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = User(
        name=user_data.name,
        email=user_data.email,
        hashed_password=hash_password(user_data.password),
        skin_type=user_data.skin_type,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    token = create_access_token({"sub": new_user.email})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": _user_dict(new_user)
    }


# ==========================================
# ROUTE 7: AUTHENTICATION — LOGIN (JSON Body)
# ==========================================
@app.post("/api/auth/login", response_model=Token)
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    """Authenticate with email + password. Returns JWT + user info."""
    user = db.query(User).filter(User.email == user_data.email).first()
    if not user or not user.hashed_password or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token({"sub": user.email})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": _user_dict(user)
    }


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
    body = await request.json()
    token = body.get("token")
    try:
        info = id_token.verify_oauth2_token(
            token, google_requests.Request(), GOOGLE_CLIENT_ID
        )
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid Google token")

    email = info.get("email")
    name = info.get("name")
    picture = info.get("picture")
    google_id = info.get("sub")

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
        # Update profile picture and google_id if missing
        if not user.google_id:
            user.google_id = google_id
        if not user.profile_picture:
            user.profile_picture = picture
        if not user.name and name:
            user.name = name
        db.commit()
        db.refresh(user)

    jwt_token = create_access_token({"sub": user.email})
    return {
        "access_token": jwt_token,
        "token_type": "bearer",
        "user": _user_dict(user)
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
    return {"total": total, "safe": safe, "moderate": moderate, "irritant": irritant, "avoid": avoid}


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