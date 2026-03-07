from sqlalchemy.orm import Session
from database import SessionLocal, engine
import models

def seed_ingredients():
    # 1. Open a manual database session
    db = SessionLocal()
    
    # 2. Define some initial "clinical" data
    # In a real project, you'd have 300+, but let's start with a solid set.
    ingredients_to_add = [
        {
            "name": "Methylparaben", 
            "safety_rating": models.SafetyRating.AVOID,
            "description": "Common preservative. Linked to endocrine disruption and skin irritation."
        },
        {
            "name": "Niacinamide", 
            "safety_rating": models.SafetyRating.SAFE,
            "description": "Vitamin B3. Helps visibly minimize enlarged pores and improve uneven skin tone."
        },
        {
            "name": "Sodium Lauryl Sulfate", 
            "safety_rating": models.SafetyRating.IRRITANT,
            "description": "Harsh foaming agent that can strip the skin of natural oils and cause dryness."
        },
        {
            "name": "Hyaluronic Acid", 
            "safety_rating": models.SafetyRating.SAFE,
            "description": "A powerful humectant that keeps skin hydrated and plump."
        }
    ]

    print("Seeding database...")

    for ing_data in ingredients_to_add:
        # Check if it already exists so we don't get 'Duplicate Entry' errors
        exists = db.query(models.Ingredient).filter(models.Ingredient.name == ing_data["name"]).first()
        if not exists:
            new_ing = models.Ingredient(**ing_data)
            db.add(new_ing)
    
    # 3. Save changes and close
    db.commit()
    db.close()
    print("Seeding complete!")

if __name__ == "__main__":
    seed_ingredients()