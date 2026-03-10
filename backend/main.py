from dotenv import load_dotenv
load_dotenv()  # Loads environment variables (like secret keys) from the .env file

from fastapi import FastAPI, Depends, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc
from typing import List

# Import your custom configurations and logic
from database import get_db, Base, engine
from models import Ingredient, SafetyRating
from ocr_service import extract_ingredients_from_image

# 1. INITIALIZE THE APP
app = FastAPI(title="Skin Lens API")

# 2. CORS (Cross-Origin Resource Sharing)
# Browsers block requests between different websites for security.
# This list tells FastAPI: "It is safe to accept requests from my local React app AND my live Netlify app."
origins = [
    "http://localhost:5173",
    "https://skin-lens.netlify.app"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, 
    allow_credentials=True,
    allow_methods=["*"],   # Allows GET, POST, PUT, DELETE, etc.
    allow_headers=["*"],   # Allows all headers (like Authorization tokens or JSON content types)
)



# ==========================================
# ROUTE 1: SEARCH & PAGINATION
# ==========================================
@app.get("/api/ingredients/search")
def search_ingredients(
    query: str = "",      # The search text (e.g., "Acid")
    risk: str = "",       # Filter by safety rating (e.g., "Safe")
    page: int = 1,        # Which page of results the user is on
    db: Session = Depends(get_db) # Automatically opens and closes the DB connection
):
    # PAGINATION MATH:
    # If limit is 12, Page 1 skips 0 ((1-1)*12). Page 2 skips 12 ((2-1)*12).
    limit = 12  
    offset = (page - 1) * limit 

    # Start a base query: "Select * from Ingredients"
    qs = db.query(Ingredient)

    

    # TEXT FILTER
    if query:
        # ilike is case-insensitive. %query% matches the word anywhere in the string.
        qs = qs.filter(Ingredient.name.ilike(f"%{query}%"))

    # RISK FILTER
    if risk and risk.strip(): 
        # Map the string (e.g., "Safe") to the actual Python Enum object
        rating_map = {r.value: r for r in SafetyRating}
        matched_enum = rating_map.get(risk)
        
        if matched_enum:
            qs = qs.filter(Ingredient.safety_rating == matched_enum)
        
        # Count total matching rows to tell the frontend how many pages there are
        total = qs.count()
        # Fetch only the 12 items for the current page
        items = qs.offset(offset).limit(limit).all()
        
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
            # Math to calculate total pages: e.g., 25 items // 12 = 2 pages + 1 remainder = 3 pages total
            "pages": (total // limit) + (1 if total % limit > 0 else 0)
        }

    # If no risk filter was used, do the same fetch and return here
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
    # 1. Read the uploaded photo
    bytes_data = await file.read()
    
    # 2. Send to your OCR/AI service. 
    # (Note: This now expects a list of dictionaries back, containing AI-generated safety ratings!)
    ingredients = extract_ingredients_from_image(bytes_data)
    
    # Fail-safe: If the image was blurry or contained no text
    if not ingredients:
        raise HTTPException(status_code=422, detail="No ingredients found in image")
    
    results = []
    
    # 3. CROSS-REFERENCE LOOP
    for ing in ingredients:
        # Check if the ingredient exists in our strict, clinical MySQL database
        matched = db.query(Ingredient).filter(
            Ingredient.name.ilike(f"%{ing['name']}%")
        ).first()
        
        

        if matched:
            # SCENARIO A: Found in Database. Use our verified clinical data.
            results.append({
                "name": matched.name,
                "safety_rating": matched.safety_rating.value,
                "description": matched.description,
                "compatible_skin_types": matched.compatible_skin_types,
                "source": "database" # Tag to let the frontend know this is highly verified
            })
        else:
            # SCENARIO B: Not in Database. Rely on the AI's best guess from the OCR service.
            results.append({
                "name": ing["name"],
                "safety_rating": ing["safety_rating"],
                "description": ing["description"],
                "compatible_skin_types": ing["compatible_skin_types"],
                "source": "ai" # Tag to let the frontend know this is AI-generated
            })

    # 4. Generate the Summary Statistics for the Dashboard Charts
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
            "unknown": 0 # Since we use AI fallback, we no longer have "unknowns"!
        }
    }

# ==========================================
# ROUTE 3: QUIZ RECOMMENDATIONS
# ==========================================
@app.post("/api/quiz/recommendations")
def get_recommendations(
    skin_type: str = Form(...),    # Data comes from an HTML Form submission 
    sensitivities: str = Form(...), 
    db: Session = Depends(get_db)
):
    # Rule 1: Only recommend 100% Safe ingredients
    qs = db.query(Ingredient).filter(Ingredient.safety_rating == SafetyRating.SAFE)
    
    # Rule 2: Must match the user's skin type OR be suitable for "All" skin types
    qs = qs.filter(or_(
        Ingredient.compatible_skin_types.ilike(f"%{skin_type}%"),
        Ingredient.compatible_skin_types.ilike("%All%")
    ))
    
    # Fetch top 5 recommendations
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

# ==========================================
# ROUTE 4: HEALTH CHECK
# ==========================================
# Cloud platforms (like Render) constantly ping this URL. 
# If it doesn't return 200 OK, the platform assumes the server crashed and restarts it.
@app.get("/health")
def health():
    return {"status": "ok"}