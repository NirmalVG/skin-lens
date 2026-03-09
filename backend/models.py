import enum

# Import specific tools to define table columns
from sqlalchemy import Column, Enum as SAEnum, Integer, String, Text

# Import 'Base' from database.py. This connects this model to the engine.
from database import Base


# ---------------------------------------------------------
# 1. THE ENUM (Enumeration)
# ---------------------------------------------------------
# Why use an Enum? It restricts the data.
# A user cannot enter "Kinda Dangerous" or "Super Safe". 
# They MUST choose one of these 4 exact options.
# We inherit 'str' so FastAPI can easily convert it to JSON text.
class SafetyRating(str, enum.Enum):
    SAFE = "Safe"
    MODERATE = "Moderate"
    IRRITANT = "Irritant"
    AVOID = "Avoid"


# ---------------------------------------------------------
# 2. THE MODEL (The Table Definition)
# ---------------------------------------------------------
class Ingredient(Base):
    # This is the actual name of the table inside MySQL
    __tablename__ = "ingredients"

    # PRIMARY KEY: The unique ID number for every ingredient (1, 2, 3...)
    # index=True makes looking up by ID very fast.
    id = Column(Integer, primary_key=True, index=True)

    # NAME: The chemical name (e.g., "Glycerin").
    # String(255) = VARCHAR(255) in SQL.
    # unique=True = No duplicates allowed. You can't add "Glycerin" twice.
    # index=True = Critical for your Search Bar! It creates a lookup table for speed.
    name = Column(String(255), unique=True, index=True)

    # SAFETY RATING: This column uses the Enum we defined above.
    # It forces the database to only accept 'Safe', 'Moderate', etc.
    # nullable=False = This field is mandatory. Every ingredient MUST have a rating.
    safety_rating = Column(SAEnum(SafetyRating, name="safety_rating_enum"), nullable=False)

    # DESCRIPTION: Holds long paragraphs. 
    # Unlike 'String', 'Text' has almost no length limit.
    description = Column(Text)

    # COMPATIBLE SKIN TYPES: A simple string like "Oily,Dry" or "All".
    # default="All" = If we forget to add a skin type, it assumes it works for everyone.
    compatible_skin_types = Column(String(255), nullable=False, default="All")