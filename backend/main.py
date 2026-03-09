from dotenv import load_dotenv
load_dotenv()  # Loads environment variables (like DB passwords) from the .env file

# Import necessary tools from FastAPI and SQLAlchemy
from fastapi import FastAPI, Depends, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc
from typing import List

# Import local modules (your own files)
from database import get_db, Base, engine
from models import Ingredient, SafetyRating
from ocr_service import extract_ingredients_from_image

# Initialize the API application
app = FastAPI(title="Skin Lens API")

# Define who is allowed to talk to this backend
# We allow localhost (for testing) and Netlify (for the live site)
origins = [
    "http://localhost:5173",
    "https://skin-lens.netlify.app"
]

# Add the "Security Guard" (CORS)
# This middleware checks every incoming request to make sure it comes from a trusted origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, 
    allow_credentials=True,
    allow_methods=["*"],    # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],    # Allow all headers (Authentication, JSON, etc.)
)

# ---------------------------------------------------------
# ENDPOINT 1: SEARCH INGREDIENTS
# Used by the frontend search bar to find chemicals manually
# ---------------------------------------------------------
@app.get("/api/ingredients/search")
def search_ingredients(
    query: str = "",      # The text the user typed (e.g., "Niacin")
    risk: str = "",       # Filter by safety (e.g., "Avoid")
    page: int = 1,        # Current page number for pagination
    db: Session = Depends(get_db) # Connect to the database
):
    limit = 12  # How many items to show per page
    offset = (page - 1) * limit # Calculate where to start reading in the DB

    # Start building the database query
    qs = db.query(Ingredient)

    # 1. Text Filter: If the user typed something, search for it
    # 'ilike' makes it case-insensitive (A = a) and % matches partial words
    if query:
        qs = qs.filter(Ingredient.name.ilike(f"%{query}%"))

    # 2. Risk Filter: If the user selected a risk category
    if risk and risk.strip(): 
        # Convert the string "Safe" into the actual Database Enum object
        rating_map = {r.value: r for r in SafetyRating}
        matched_enum = rating_map.get(risk)
        
        if matched_enum:
            qs = qs.filter(Ingredient.safety_rating == matched_enum)
        
        # Calculate totals for pagination
        total = qs.count()
        items = qs.offset(offset).limit(limit).all()
        
        # Return the filtered results immediately
        return {
            "items": [
                {
                    "id": i.id,
                    "name": i.name,
                    "safety_rating": i.safety_rating.value,
                    "description": i.description,
                    "compatible_skin_types": i.compatible_skin_types
                } for i in items
            ],
            "total": total,
            "page": page,
            # Calculate total pages needed
            "pages": (total // limit) + (1 if total % limit > 0 else 0)
        }

    # 3. Default Fetch: If no risk filter was applied, run the query here
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

# ---------------------------------------------------------
# ENDPOINT 2: ANALYZE IMAGE
# The core feature: Takes a photo -> OCR -> Database Match
# ---------------------------------------------------------
@app.post("/api/analyze/image")
async def analyze_label(file: UploadFile = File(...), db: Session = Depends(get_db)):
    # 1. Read the raw image file uploaded by the user
    bytes_data = await file.read()
    
    # 2. Send image to OCR Service to get a list of text strings (e.g., ["Aqua", "Glycerin"])
    extracted_names = extract_ingredients_from_image(bytes_data)
    
    results = []
    
    # 3. Loop through every word found by the OCR
    for name in extracted_names:
        # Check if this word exists in our SQL Database
        matched = db.query(Ingredient).filter(Ingredient.name.ilike(f"%{name}%")).first()
        
        if matched:
            # If found, add the clinical details (Safety, Description)
            results.append({
                "name": matched.name,
                "safety_rating": matched.safety_rating.value,
                "description": matched.description
            })
        else:
            # If not found, mark it as Unknown
            results.append({
                "name": name,
                "safety_rating": "Unknown",
                "description": "Not found in our clinical database."
            })
            
    # 4. Calculate Statistics (How many "Avoid", how many "Safe", etc.)
    avoid_count = sum(1 for r in results if r["safety_rating"] == "Avoid")
    irritant_count = sum(1 for r in results if r["safety_rating"] == "Irritant")
    moderate_count = sum(1 for r in results if r["safety_rating"] == "Moderate")
    safe_count = sum(1 for r in results if r["safety_rating"] == "Safe")
    unknown_count = sum(1 for r in results if r["safety_rating"] == "Unknown")
    
    # 5. Return the full report to the frontend
    return {
        "ingredients": results,
        "extracted_raw_count": len(extracted_names),
        "summary": {
            "avoid": avoid_count,
            "irritant": irritant_count,
            "moderate": moderate_count,
            "safe": safe_count,
            "unknown": unknown_count
        }
    }

# ---------------------------------------------------------
# ENDPOINT 3: SKIN QUIZ
# Recommends ingredients based on user skin type
# ---------------------------------------------------------
@app.post("/api/quiz/recommendations")
def get_recommendations(
    skin_type: str = Form(...),      # e.g., "Oily", "Dry"
    sensitivities: str = Form(...),  # e.g., "Acne", "None"
    db: Session = Depends(get_db)
):
    # 1. Start by finding ONLY ingredients marked as SAFE
    qs = db.query(Ingredient).filter(Ingredient.safety_rating == SafetyRating.SAFE)
    
    # 2. Filter for ingredients compatible with the user's specific skin type
    # OR ingredients that work for "All" skin types
    qs = qs.filter(or_(
        Ingredient.compatible_skin_types.ilike(f"%{skin_type}%"),
        Ingredient.compatible_skin_types.ilike("%All%")
    ))
    
    # 3. Get the top 5 results
    top_ingredients = qs.limit(5).all()
    
    return {
        "skin_type": skin_type,
        "recommended_ingredients": [
            {
                "name": i.name,
                "description": i.description
            } for i in top_ingredients
        ]
    }

# ---------------------------------------------------------
# ENDPOINT 4: HEALTH CHECK
# Used by Render to check if the server is alive
# ---------------------------------------------------------
@app.get("/health")
def health():
    return {"status": "ok"}