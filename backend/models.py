import enum

from sqlalchemy import Column, Enum as SAEnum, Integer, String, Text

from database import Base


class SafetyRating(str, enum.Enum):
    SAFE = "Safe"
    MODERATE = "Moderate"
    IRRITANT = "Irritant"
    AVOID = "Avoid"


class Ingredient(Base):
    __tablename__ = "ingredients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True)
    safety_rating = Column(SAEnum(SafetyRating, name="safety_rating_enum"), nullable=False)
    description = Column(Text)
    compatible_skin_types = Column(String(255), nullable=False, default="All")