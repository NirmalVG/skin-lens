import enum
from datetime import datetime, timezone

from sqlalchemy import Column, Enum as SAEnum, Integer, String, Text, DateTime

from database import Base


# ---------------------------------------------------------
# USER MODEL (Authentication)
# ---------------------------------------------------------
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=True)  # nullable for Google-only users
    google_id = Column(String(255), nullable=True)
    profile_picture = Column(String(512), nullable=True)
    skin_type = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


# ---------------------------------------------------------
# 1. THE ENUM (Enumeration)
# ---------------------------------------------------------
class SafetyRating(str, enum.Enum):
    SAFE = "Safe"
    MODERATE = "Moderate"
    IRRITANT = "Irritant"
    AVOID = "Avoid"


# ---------------------------------------------------------
# 2. THE INGREDIENT MODEL
# ---------------------------------------------------------
class Ingredient(Base):
    __tablename__ = "ingredients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True)
    safety_rating = Column(SAEnum(SafetyRating, name="safety_rating_enum"), nullable=False)
    description = Column(Text)
    compatible_skin_types = Column(String(255), nullable=False, default="All")