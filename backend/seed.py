from sqlalchemy.pool import NullPool
import time

from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError

from database import Base, engine, SessionLocal
import models
from ingredients_data import INGREDIENTS

RATING_MAP = {
    "Safe": models.SafetyRating.SAFE,
    "Moderate": models.SafetyRating.MODERATE,
    "Irritant": models.SafetyRating.IRRITANT,
    "Avoid": models.SafetyRating.AVOID,
}

BATCH_SIZE = 25
MAX_RETRIES = 3

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"ssl": {"check_hostname": False, "verify_mode": 0}},
    poolclass=NullPool  # Closes connection immediately after each use
)


def seed_ingredients():
    Base.metadata.create_all(bind=engine)

    # Deduplicate by name, keep first occurrence
    seen = set()
    ingredients_to_add = []
    for ing in INGREDIENTS:
        if ing["name"] not in seen:
            seen.add(ing["name"])
            ingredients_to_add.append(ing)
        if len(ingredients_to_add) >= 350:
            break

    print(f"Seeding database with {len(ingredients_to_add)} ingredients...")

    for attempt in range(MAX_RETRIES):
        try:
            db = SessionLocal()
            added = 0
            for i, ing_data in enumerate(ingredients_to_add):
                exists = db.query(models.Ingredient).filter(models.Ingredient.name == ing_data["name"]).first()
                if not exists:
                    data = {
                        "name": ing_data["name"],
                        "safety_rating": RATING_MAP.get(ing_data["safety_rating"], models.SafetyRating.SAFE),
                        "description": ing_data.get("description") or "",
                        "compatible_skin_types": ing_data.get("compatible_skin_types", "All"),
                    }
                    db.add(models.Ingredient(**data))
                    added += 1

                if (i + 1) % BATCH_SIZE == 0:
                    db.commit()

            db.commit()
            db.close()
            print(f"Seeding complete! Added {added} ingredients.")
            return
        except OperationalError as e:
            if hasattr(e.orig, "args") and e.orig.args[0] == 1213:
                db.rollback()
                db.close()
                if attempt < MAX_RETRIES - 1:
                    print(f"Deadlock detected, retrying in 2s (attempt {attempt + 2}/{MAX_RETRIES})...")
                    time.sleep(2)
                else:
                    raise
            else:
                raise

if __name__ == "__main__":
    seed_ingredients()