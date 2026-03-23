# Import tools needed to talk to the database and manage connections
from sqlalchemy.pool import NullPool
from sqlalchemy import create_engine
import os
import re
import time

# Load environment variables (like your DATABASE_URL) from the local .env file
from dotenv import load_dotenv
load_dotenv()

# Import Session for managing database transactions, and OperationalError to catch database crashes
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError

# Import your custom database setups, your data models, and the massive list of ingredients to insert
from database import Base, SessionLocal
import models
from ingredients_data import INGREDIENTS

# ==========================================
# 1. DATABASE CONNECTION SETUP
# ==========================================
# We recreate the exact engine setup from database.py here so the seed script can run entirely on its own.
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "")

# Fix the URL format for SQLAlchemy to use the pymysql driver
if SQLALCHEMY_DATABASE_URL.startswith("mysql://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("mysql://", "mysql+pymysql://", 1)

# Strip out strict SSL requirements from the connection string
SQLALCHEMY_DATABASE_URL = re.sub(r'[?&]ssl[_-]mode=\w+', '', SQLALCHEMY_DATABASE_URL)

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    # connect_args relax SSL rules so cloud databases don't reject the connection
    connect_args={"ssl": {"check_hostname": False, "verify_mode": 0}}, 
    # NullPool forces the script to open a fresh connection every time, preventing 
    # idle connection timeouts when pushing a lot of data.
    poolclass=NullPool  
)

# ==========================================
# 2. CONFIGURATION & MAPPING
# ==========================================
# A dictionary to translate the string ratings from your raw data file 
# into the strict Enum objects required by your database model.
RATING_MAP = {
    "Safe": models.SafetyRating.SAFE,
    "Moderate": models.SafetyRating.MODERATE,
    "Irritant": models.SafetyRating.IRRITANT,
    "Avoid": models.SafetyRating.AVOID,
}

# Instead of trying to insert all 350 ingredients at the exact same millisecond 
# (which can crash a cheap cloud database), we save them in batches of 25.
BATCH_SIZE = 25

# If the database locks up, we will try to run the script 3 times before finally giving up.
MAX_RETRIES = 3

# ==========================================
# 3. THE CORE SEEDING LOGIC
# ==========================================
def seed_ingredients():
    # Force SQLAlchemy to check the database and create the 'ingredients' table if it doesn't exist
    Base.metadata.create_all(bind=engine)

    # A "set" is a mathematical list that can only contain unique items. 
    # We use it to ensure we don't accidentally try to insert two ingredients with the exact same name.
    seen = set() 
    ingredients_to_add = []
    
    # Loop through the raw data file
    for ing in INGREDIENTS:
        # Deduplication check: Have we seen this name before?
        if ing["name"] not in seen:
            seen.add(ing["name"])
            ingredients_to_add.append(ing)
        
        # Stop at 350 to prevent overloading a free-tier database limits
        if len(ingredients_to_add) >= 350:
            break

    print(f"Seeding database with {len(ingredients_to_add)} ingredients...")

    # Start the retry loop. It will try 3 times.
    for attempt in range(MAX_RETRIES):
        try:
            # Open a fresh database session
            db = SessionLocal() 
            added = 0
            
            # Loop through the clean, deduplicated list we built earlier
            for i, ing_data in enumerate(ingredients_to_add):
                
                # Double-check the ACTUAL database: Does this ingredient already exist in the table?
                # This prevents errors if you run the seed script twice.
                exists = db.query(models.Ingredient).filter(models.Ingredient.name == ing_data["name"]).first()
                
                if not exists:
                    # Prepare the data dictionary, using .get() to provide safe fallbacks 
                    # if the raw data is missing a description or skin type.
                    data = {
                        "name": ing_data["name"],
                        "safety_rating": RATING_MAP.get(ing_data["safety_rating"], models.SafetyRating.SAFE),
                        "description": ing_data.get("description") or "",
                        "compatible_skin_types": ing_data.get("compatible_skin_types", "All"),
                    }
                    
                    # Convert the dictionary into a SQLAlchemy Ingredient object and stage it for saving
                    # (**data unpacks the dictionary into keyword arguments)
                    db.add(models.Ingredient(**data)) 
                    added += 1

                # If we have staged 25 new ingredients, commit (save) them to the database now.
                # This keeps memory usage low and prevents the database from getting overwhelmed.
                if (i + 1) % BATCH_SIZE == 0:
                    db.commit()
            
            # Catch any leftover ingredients that didn't fit perfectly into a batch of 25
            db.commit()
            
            # Close the connection and report success!
            db.close() 
            print(f"Seeding complete! Added {added} ingredients.")
            
            # Exit the retry loop entirely, the job is done.
            return 

        # ==========================================
        # 4. ERROR HANDLING & DEADLOCK RECOVERY
        # ==========================================
        except OperationalError as e:
            # MySQL Error 1213 is a "Deadlock". It happens when two database processes 
            # try to edit the same data at the exact same time, and MySQL panics and crashes one of them.
            if hasattr(e.orig, "args") and e.orig.args[0] == 1213:
                # Discard all unsaved changes to prevent corrupt data
                db.rollback() 
                db.close()    
                
                # If we haven't hit our max retry limit yet...
                if attempt < MAX_RETRIES - 1:
                    print(f"Deadlock detected, retrying in 2s (attempt {attempt + 2}/{MAX_RETRIES})...")
                    # Wait 2 seconds for the database to calm down before trying the loop again
                    time.sleep(2)
                else:
                    # We hit max retries, throw the error and crash the script
                    raise 
            else:
                # It was a different database error (like a bad password or lost connection), crash immediately
                raise 


# This block ensures the script only runs if you type `python seed.py` in the terminal.
# It prevents the script from accidentally running if you import it into another file.
if __name__ == "__main__":
    seed_ingredients()