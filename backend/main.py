# ==========================================
# 1. IMPORTS & SETUP
# ==========================================
# dotenv loads environment variables (like API keys) from a .env file into the system
from dotenv import load_dotenv
import os
load_dotenv()

# BaseModel from Pydantic is used to strictly define the shape of incoming JSON data
from pydantic import BaseModel

# 'or_' allows SQLAlchemy to run SQL queries that say "WHERE condition_a OR condition_b"
from sqlalchemy import or_

# FastAPI core tools for building the API, handling files, checking errors, and accessing the raw request
from fastapi import FastAPI, Depends, UploadFile, File, Form, HTTPException, Request
# CORSMiddleware acts as a security bouncer, deciding which external websites can talk to this API
from fastapi.middleware.cors import CORSMiddleware
# Session is the active database connection
from sqlalchemy.orm import Session

# Import custom functions and models from your other files
from database import get_db, Base, engine
from auth import create_access_token, get_current_user
from ocr_service import extract_ingredients_from_image
from models import Ingredient, SafetyRating, User, QuizResult
import requests

# ==========================================
# 2. SCHEMAS (Data Shapes)
# ==========================================
# Defines exactly what JSON React must send when submitting a quiz
class QuizRequest(BaseModel):
    skin_type: str
    sensitivities: str = "none" # Default to "none" if React forgets to send this field

# ==========================================
# 3. APP INITIALIZATION
# ==========================================
app = FastAPI(title="Skin Lens API")

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")

# @app.on_event("startup") runs exactly once when the server boots up
@app.on_event("startup")
def on_startup():
    try:
        # Base.metadata.create_all reads your models.py file and automatically creates 
        # the corresponding SQL tables in the database if they don't exist yet.
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables verified / created.")
    except Exception as e:
        print(f"⚠️  Could not auto-create tables (DB may be unreachable): {e}")

# ==========================================
# 4. MIDDLEWARE (Traffic Control)
# ==========================================
# A list of specific React frontend URLs allowed to make requests to this backend
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
    allow_credentials=True, # Allows cookies and Authentication headers to be sent
    allow_methods=["*"],    # Allows all HTTP methods (GET, POST, PUT, DELETE)
    allow_headers=["*"],
    expose_headers=["Authorization"], # Lets the frontend specifically read the Auth header
)

# This custom middleware injects a special security header into every single response.
# This header is strictly required by Google's new OAuth popup system to prevent cross-site hacking.
@app.middleware("http")
async def add_coop_header(request, call_next):
    response = await call_next(request)
    response.headers["Cross-Origin-Opener-Policy"] = "same-origin-allow-popups"
    return response

# ==========================================
# 5. HELPER FUNCTIONS
# ==========================================
def _user_dict(user: User) -> dict:
    """A helper tool to convert a SQLAlchemy User object into a clean dictionary, 
    ensuring sensitive data (like passwords) isn't accidentally leaked to the frontend."""
    return {
        "id":        user.id,
        "name":      user.name      or "",
        "email":     user.email     or "",
        "picture":   user.profile_picture or "",
    }

# ==========================================
# 6. PUBLIC ROUTES (No Login Required)
# ==========================================

@app.get("/api/ingredients/search")
def search_ingredients(
    query: str = "", # What the user typed in the search bar
    risk: str = "",  # The filter button they clicked (e.g., "Safe")
    page: int = 1,   # The current pagination page number
    db: Session = Depends(get_db)
):
    """Searches the database for ingredients, applying pagination and filters."""
    limit = 12 # Show exactly 12 cards per page
    offset = (page - 1) * limit # Calculate how many cards to skip for the current page

    # Start a generic query asking for all ingredients
    qs = db.query(Ingredient)

    # If the user typed a query, add a SQL ILIKE condition (case-insensitive search)
    if query:
        qs = qs.filter(Ingredient.name.ilike(f"%{query}%"))

    # If the user clicked a risk filter, apply it
    if risk and risk.strip():
        # Convert the string "Safe" into the database Enum object SafetyRating.SAFE
        rating_map = {r.value: r for r in SafetyRating}
        matched_enum = rating_map.get(risk)
        if matched_enum:
            qs = qs.filter(Ingredient.safety_rating == matched_enum)

    total = qs.count() # Total number of items that match the filters
    items = qs.offset(offset).limit(limit).all() # The 12 specific items for this page

    # Package everything up in a neat JSON response
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


@app.post("/api/analyze/image")
async def analyze_label(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """The core Scanner feature. Receives an image, reads the text via OCR, and cross-references the DB."""
    # Convert the uploaded file into raw bytes
    bytes_data = await file.read()
    
    # Send the bytes to the external OCR service (Google Vision/Tesseract)
    ingredients = extract_ingredients_from_image(bytes_data)

    if not ingredients:
        raise HTTPException(status_code=422, detail="No ingredients found in image")

    results = []

    # Loop through every text string the OCR found
    for ing in ingredients:
        # Search our local database to see if we have clinical data on this chemical
        matched = db.query(Ingredient).filter(
            Ingredient.name.ilike(f"%{ing['name']}%")
        ).first()

        # If we found it in our DB, return our clinical data
        if matched:
            results.append({
                "name": matched.name,
                "safety_rating": matched.safety_rating.value,
                "description": matched.description,
                "compatible_skin_types": matched.compatible_skin_types,
                "source": "database"
            })
        # If we didn't find it, return the AI's fallback analysis
        else:
            results.append({
                "name": ing["name"],
                "safety_rating": ing["safety_rating"],
                "description": ing["description"],
                "compatible_skin_types": ing["compatible_skin_types"],
                "source": ing.get("source", "ai")  
            })

    # Tally up the final toxicity scores to build the chart on the frontend
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


@app.post("/api/quiz/recommendations")
def get_recommendations(
    data: QuizRequest, # Expects the JSON structure we defined at the top
    db: Session = Depends(get_db)
):
    """Calculates product recommendations based on a quick quiz, no login required."""
    # Start by grabbing ALL ingredients marked as completely "Safe"
    qs = db.query(Ingredient).filter(Ingredient.safety_rating == SafetyRating.SAFE)
    
    # Filter that safe list down to only ingredients that match the user's skin type OR are marked for "All"
    qs = qs.filter(or_(
        Ingredient.compatible_skin_types.ilike(f"%{data.skin_type}%"),
        Ingredient.compatible_skin_types.ilike("%All%")
    ))
    
    # Grab the top 5 results
    top_ingredients = qs.limit(5).all()

    return {
        "skin_type": data.skin_type,
        "recommended_ingredients": [{
            "name": i.name,
            "description": i.description
        } for i in top_ingredients]
    }


@app.get("/health")
def health():
    """A tiny ping endpoint used by hosting services (like Render/Heroku) to make sure the server hasn't crashed."""
    return {"status": "ok"}


# ==========================================
# 7. AUTHENTICATION ROUTES
# ==========================================

@app.get("/api/auth/me")
def get_me(current_user: User = Depends(get_current_user)):
    """Returns the user profile. Depends(get_current_user) acts as a bouncer, 
    rejecting the request if the user didn't send a valid JWT token."""
    return _user_dict(current_user)


@app.post("/api/auth/google")
async def google_auth(request: Request, db: Session = Depends(get_db)):
    """Takes a raw Google token from the React frontend, validates it directly with Google, and logs the user in."""
    body  = await request.json()
    token = body.get("token")

    if not token:
        raise HTTPException(status_code=400, detail="Token missing")

    try:
        # Call Google's official API to say "Hey, is this token actually real?"
        response = requests.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {token}"}
        )
        info = response.json() 
    except Exception as e:
        raise HTTPException(status_code=400, detail="Could not reach Google")

    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="Invalid Google token")

    # If Google says yes, extract the user's info
    email     = info.get("email")
    name      = info.get("name")
    picture   = info.get("picture")
    google_id = info.get("sub")

    if not email:
        raise HTTPException(status_code=400, detail="Could not get email from Google")

    try:
        # Check if we already have an account for this email in our database
        user = db.query(User).filter(User.email == email).first()
        
        # If not, create a brand new user account
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
            
        # If they exist, silently update their profile picture and Google ID if they were missing
        else:
            if not user.google_id:
                user.google_id = google_id
            if not user.profile_picture:
                user.profile_picture = picture
            db.commit()
            db.refresh(user)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail="Database error")

    # Create OUR backend's custom JWT token to hand to React
    jwt_token = create_access_token({"sub": user.email})
    
    return {
        "access_token": jwt_token,
        "token_type":   "bearer",
        "user":         _user_dict(user)
    }


# ==========================================
# 8. ADMIN DASHBOARD ROUTES
# ==========================================
# (Note: In production, these should ALSO have Depends(get_current_user) and a check for admin privileges)

@app.get("/api/admin/stats")
def admin_stats(db: Session = Depends(get_db)):
    """Counts up database rows to build the charts on the Admin dashboard."""
    total = db.query(Ingredient).count()
    safe = db.query(Ingredient).filter(Ingredient.safety_rating == SafetyRating.SAFE).count()
    moderate = db.query(Ingredient).filter(Ingredient.safety_rating == SafetyRating.MODERATE).count()
    irritant = db.query(Ingredient).filter(Ingredient.safety_rating == SafetyRating.IRRITANT).count()
    avoid = db.query(Ingredient).filter(Ingredient.safety_rating == SafetyRating.AVOID).count()
    users = db.query(User).count()  
    return {
        "total": total, "safe": safe, "moderate": moderate,
        "irritant": irritant, "avoid": avoid,
        "total_users": users 
    }

@app.post("/api/admin/ingredient")
def add_ingredient(
    # Because this route uses 'Form(...)', React MUST send a FormData() object, not JSON
    name: str = Form(...),
    safety_rating: str = Form(...),
    description: str = Form(""),
    compatible_skin_types: str = Form("All"),
    db: Session = Depends(get_db)
):
    """Allows an admin to manually add a new chemical to the Encyclopedia."""
    # Convert the string rating ("Safe") into the actual Database Enum
    rating_map = {r.value: r for r in SafetyRating}
    rating = rating_map.get(safety_rating)
    if not rating:
        raise HTTPException(status_code=400, detail="Invalid safety rating")

    # Prevent accidental duplicates
    existing = db.query(Ingredient).filter(Ingredient.name == name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Ingredient already exists")

    # Create and save the new ingredient
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

@app.put("/api/admin/ingredient/{ingredient_id}")
async def update_ingredient(
    ingredient_id: int,  # The ID from the URL path (e.g., /api/admin/ingredient/45)
    request: Request,
    db: Session = Depends(get_db)
):
    """Allows an admin to edit an existing ingredient."""
    # First, find the ingredient to make sure it exists
    ing = db.query(Ingredient).filter(Ingredient.id == ingredient_id).first()
    if not ing:
        raise HTTPException(status_code=404, detail="Ingredient not found")

    body = await request.json()

    # Update only the fields the admin actually changed
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


@app.delete("/api/admin/ingredient/{ingredient_id}")
def delete_ingredient(ingredient_id: int, db: Session = Depends(get_db)):
    """Permanently deletes an ingredient from the database."""
    ing = db.query(Ingredient).filter(Ingredient.id == ingredient_id).first()
    if not ing:
        raise HTTPException(status_code=404, detail="Ingredient not found")
    db.delete(ing)
    db.commit()
    return {"message": "Ingredient deleted"}


# ==========================================
# 9. PROTECTED QUIZ ROUTES
# ==========================================

@app.post("/api/quiz/save")
def save_quiz_result(
    data: QuizRequest, # Uses JSON
    db: Session = Depends(get_db),
    # Depends(get_current_user) forces the user to be logged in to save a result
    current_user: User = Depends(get_current_user) 
):
    """Saves a user's quiz result to their profile so they can see it later."""
    # Check if they took the quiz before
    old = db.query(QuizResult).filter(
        QuizResult.user_id == current_user.id
    ).first()
    
    # We only let users have one active profile, so delete the old one
    if old:
        db.delete(old)

    # Save the new profile
    result = QuizResult(
        user_id=current_user.id,
        skin_type=data.skin_type,
        sensitivities=data.sensitivities,
    )
    
    db.add(result)
    db.commit()
    db.refresh(result)
    
    return {"message": "Quiz result saved", "skin_type": data.skin_type}


@app.get("/api/quiz/my-result")
def get_my_quiz_result(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Fetches a logged-in user's previously saved quiz profile when they visit the app."""
    result = db.query(QuizResult).filter(
        QuizResult.user_id == current_user.id
    ).first()

    if not result:
        return {"has_result": False}

    # Recalculate fresh recommendations based on their saved skin type
    qs = db.query(Ingredient).filter(
        Ingredient.safety_rating == SafetyRating.SAFE
    ).filter(or_(
        Ingredient.compatible_skin_types.ilike(f"%{result.skin_type}%"),
        Ingredient.compatible_skin_types.ilike("%All%")
    )).limit(5).all()

    return {
        "has_result":   True,
        "skin_type":    result.skin_type,
        "taken_on":     result.created_at.strftime("%B %d, %Y"), # Formats date nicely
        "recommended_ingredients": [
            {"name": i.name, "description": i.description}
            for i in qs
        ]
    }

@app.get("/api/admin/users")
def get_all_users(db: Session = Depends(get_db)):
    """Admin endpoint to see a list of everyone registered on the site, newest first."""
    users = db.query(User).order_by(User.created_at.desc()).all()
    # Uses the helper function to clean the data before sending it to React
    return [_user_dict(u) for u in users]