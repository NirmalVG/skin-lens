from dotenv import load_dotenv
load_dotenv()
from sqlalchemy import cast, String
from fastapi import FastAPI, Depends, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc
from typing import List

from database import get_db, Base, engine
from models import Ingredient, SafetyRating
from ocr_service import extract_ingredients_from_image

app = FastAPI(title="PureCheck AI API")

origins = [
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, 
    allow_credentials=True,
    allow_methods=["*"],    
    allow_headers=["*"],    
)

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

    if risk:
    # Skip ORM enum comparison entirely — use raw SQL string match
        from sqlalchemy import text
        all_items = [i for i in qs.all() if i.safety_rating.value == risk]
        total = len(all_items)
        items = all_items[offset:offset + limit]
        # Return early
        return {
            "items": [{"id": i.id, "name": i.name, "safety_rating": i.safety_rating.value,
                    "description": i.description, "compatible_skin_types": i.compatible_skin_types}
                    for i in items],
            "total": total, "page": page,
            "pages": (total // limit) + (1 if total % limit > 0 else 0)
    }

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

@app.post("/api/analyze/image")
async def analyze_label(file: UploadFile = File(...), db: Session = Depends(get_db)):
    bytes_data = await file.read()
    extracted_names = extract_ingredients_from_image(bytes_data)
    
    results = []
    
    for name in extracted_names:
        matched = db.query(Ingredient).filter(Ingredient.name.ilike(f"%{name}%")).first()
        if matched:
            results.append({
                "name": matched.name,
                "safety_rating": matched.safety_rating.value,
                "description": matched.description
            })
        else:
            results.append({
                "name": name,
                "safety_rating": "Unknown",
                "description": "Not found in our clinical database."
            })
            
    avoid_count = sum(1 for r in results if r["safety_rating"] == "Avoid")
    irritant_count = sum(1 for r in results if r["safety_rating"] == "Irritant")
    moderate_count = sum(1 for r in results if r["safety_rating"] == "Moderate")
    safe_count = sum(1 for r in results if r["safety_rating"] == "Safe")
    unknown_count = sum(1 for r in results if r["safety_rating"] == "Unknown")
    
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

@app.post("/api/quiz/recommendations")
def get_recommendations(skin_type: str = Form(...), sensitivities: str = Form(...), db: Session = Depends(get_db)):
    # Find safe ingredients compatible with the skin type
    qs = db.query(Ingredient).filter(Ingredient.safety_rating == SafetyRating.SAFE)
    
    # We query skin types that contain the chosen skin type or "All"
    qs = qs.filter(or_(
        Ingredient.compatible_skin_types.ilike(f"%{skin_type}%"),
        Ingredient.compatible_skin_types.ilike("%All%")
    ))
    
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

