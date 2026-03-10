from sqlalchemy.pool import NullPool
from sqlalchemy import create_engine
import os
import re
import time
from dotenv import load_dotenv

# 1. LOAD ENVIRONMENT VARIABLES
load_dotenv()

from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError

# Import your local files
from database import Base, SessionLocal
import models
from ingredients_data import INGREDIENTS

# ==========================================
# 2. CLOUD DATABASE URL FIXES
# ==========================================
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "")

# Fix the driver: SQLAlchemy needs 'pymysql' to talk to MySQL.
if SQLALCHEMY_DATABASE_URL.startswith("mysql://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("mysql://", "mysql+pymysql://", 1)

# Clean the URL: Remove conflicting SSL arguments from the URL string.
SQLALCHEMY_DATABASE_URL = re.sub(r'[?&]ssl[_-]mode=\w+', '', SQLALCHEMY_DATABASE_URL)

# ==========================================
# 3. ENGINE CONFIGURATION
# ==========================================
# (Note: You defined engine twice in your code, which is fine, but only the last one is used!)
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"ssl": {"check_hostname": False, "verify_mode": 0}}, # Accept cloud SSL certs
    poolclass=NullPool  # Closes connection immediately after each use to prevent timeouts
)

# ==========================================
# 4. DATA MAPPING & SETTINGS
# ==========================================
# Maps the string words from your INGREDIENTS list to the strict Python Enums in your Models
RATING_MAP = {
    "Safe": models.SafetyRating.SAFE,
    "Moderate": models.SafetyRating.MODERATE,
    "Irritant": models.SafetyRating.IRRITANT,
    "Avoid": models.SafetyRating.AVOID,
}

# BATCH_SIZE: How many ingredients to save at one time. 
# MAX_RETRIES: How many times to try again if the database crashes.
BATCH_SIZE = 25
MAX_RETRIES = 3

# ==========================================
# 5. THE MAIN SEEDER FUNCTION
# ==========================================
def seed_ingredients():
    # Automatically create the 'ingredients' table in MySQL if it doesn't exist yet
    Base.metadata.create_all(bind=engine)

    # --- STEP A: DEDUPLICATION ---
    seen = set() # A Python 'set' is super fast for checking if something already exists
    ingredients_to_add = []
    
    # Loop through the raw data. If we haven't 'seen' the name yet, add it.
    for ing in INGREDIENTS:
        if ing["name"] not in seen:
            seen.add(ing["name"])
            ingredients_to_add.append(ing)
        
        # Stop once we have exactly 350 unique ingredients
        if len(ingredients_to_add) >= 350:
            break

    print(f"Seeding database with {len(ingredients_to_add)} ingredients...")

    # --- STEP B: THE RETRY LOOP (Deadlock Handling) ---
    # Cloud databases sometimes lock up. This loop says: "Try 3 times before giving up."
    for attempt in range(MAX_RETRIES):
        try:
            db = SessionLocal() # Open a database connection
            added = 0
            
            # enumerate gives us an index (i) and the data (ing_data)
            for i, ing_data in enumerate(ingredients_to_add):
                
                # Check if this specific ingredient is ALREADY in the MySQL database
                exists = db.query(models.Ingredient).filter(models.Ingredient.name == ing_data["name"]).first()
                
                if not exists:
                    # Format the data to match our SQLAlchemy Model exactly
                    data = {
                        "name": ing_data["name"],
                        # Use the map to get the Enum. If not found, default to SAFE.
                        "safety_rating": RATING_MAP.get(ing_data["safety_rating"], models.SafetyRating.SAFE),
                        "description": ing_data.get("description") or "",
                        "compatible_skin_types": ing_data.get("compatible_skin_types", "All"),
                    }
                    db.add(models.Ingredient(**data)) # Stage the data to be saved
                    added += 1

                # --- STEP C: BATCH COMMITTING ---
                # Every 25 items, push the data to the database.
                if (i + 1) % BATCH_SIZE == 0:
                    db.commit()
            
            

            # Final commit for any leftovers (e.g., if we had 30 items, the last 5 commit here)
            db.commit()
            db.close() # Clean up the connection
            print(f"Seeding complete! Added {added} ingredients.")
            
            return # SUCCESS! Exit the function.

        # --- STEP D: ERROR HANDLING ---
        except OperationalError as e:
            # Error 1213 is the specific MySQL code for a "Deadlock"
            if hasattr(e.orig, "args") and e.orig.args[0] == 1213:
                db.rollback() # Undo the current batch to prevent data corruption
                db.close()    # Close the locked connection
                
                # If we haven't hit our 3-try limit yet, wait 2 seconds and try again
                if attempt < MAX_RETRIES - 1:
                    print(f"Deadlock detected, retrying in 2s (attempt {attempt + 2}/{MAX_RETRIES})...")
                    time.sleep(2)
                else:
                    raise # We tried 3 times and failed. Crash the program.
            else:
                raise # It was a different OperationalError (like wrong password). Crash immediately.



if __name__ == "__main__":
    seed_ingredients() # Run the script when executed from the terminal