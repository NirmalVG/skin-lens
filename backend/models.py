import enum

# Import the column types and constraints we need from SQLAlchemy to define our table structures
from sqlalchemy import Column, Integer, String, Text, DateTime, Enum as SAEnum
# 'func' allows us to use built-in SQL database functions (like getting the current time)
from sqlalchemy.sql import func

# Import the 'Base' class we created in database.py. 
# Every model must inherit from this Base so SQLAlchemy knows it represents a database table.
from database import Base

# ==========================================
# 1. USER MODEL
# ==========================================
class User(Base):
    # __tablename__ tells SQLAlchemy exactly what to name this table in the PostgreSQL/MySQL database
    __tablename__ = "users"

    # id: The primary key is the unique identifier for each row (1, 2, 3...).
    # index=True makes the database build a fast-lookup index for this column.
    id              = Column(Integer, primary_key=True, index=True)
    
    # name: A standard text string up to 255 characters. 
    # nullable=True means it's okay if a user doesn't provide a name.
    name            = Column(String(255), nullable=True)
    
    # email: unique=True ensures no two users can register with the exact same email.
    # nullable=False means this field is strictly required; a user cannot exist without an email.
    email           = Column(String(255), unique=True, index=True, nullable=False)
    
    # hashed_password: Stores the scrambled password. It is nullable because users logging in 
    # via Google OAuth won't have a traditional password in our database.
    hashed_password = Column(String(255), nullable=True)
    
    # google_id: Stores the unique Google account ID if they used "Continue with Google".
    google_id       = Column(String(255), nullable=True)
    
    # profile_picture: A longer string (512 chars) to hold the URL of the user's Google avatar.
    profile_picture = Column(String(512), nullable=True)
    
    # skin_type: Caches the user's skin type (e.g., "Oily", "Dry") directly on their profile.
    skin_type       = Column(String(50), nullable=True)
    
    # created_at: Automatically records the exact date and time the user registered.
    # server_default=func.now() tells the actual database engine (not Python) to timestamp it.
    created_at      = Column(DateTime, server_default=func.now())


# ==========================================
# 2. INGREDIENT ENUM & MODEL
# ==========================================

# This is a standard Python Enum. It strictly limits the values that can be assigned 
# to a safety rating. If someone tries to save a rating of "Kinda Safe", Python will block it.
class SafetyRating(str, enum.Enum):
    SAFE = "Safe"
    MODERATE = "Moderate"
    IRRITANT = "Irritant"
    AVOID = "Avoid"

class Ingredient(Base):
    __tablename__ = "ingredients"

    id = Column(Integer, primary_key=True, index=True)
    
    # name: unique=True ensures we don't accidentally add "Niacinamide" to the encyclopedia twice.
    name = Column(String(255), unique=True, index=True)
    
    # safety_rating: We use SAEnum (SQLAlchemy Enum) to map our Python Enum to the database.
    # nullable=False means every ingredient MUST have a rating.
    safety_rating = Column(SAEnum(SafetyRating, name="safety_rating_enum"), nullable=False)
    
    # description: Column(Text) is used instead of String when we expect long paragraphs of text.
    description = Column(Text)
    
    # compatible_skin_types: A simple string listing who can use it. 
    # default="All" ensures that if we forget to specify skin types, it defaults to being universally safe.
    compatible_skin_types = Column(String(255), nullable=False, default="All")


# ==========================================
# 3. QUIZ RESULTS MODEL
# ==========================================
class QuizResult(Base):
    __tablename__ = "quiz_results"

    id           = Column(Integer, primary_key=True, index=True)
    
    # user_id: This links the quiz result to a specific user profile (Foreign Key concept).
    # index=True makes it very fast to look up "All quiz results for User #5".
    user_id      = Column(Integer, nullable=False, index=True)
    
    # skin_type: The primary outcome of the quiz (e.g., "Combination").
    skin_type    = Column(String(100), nullable=False)
    
    # sensitivities: Stores any specific allergies or issues the user flagged during the quiz.
    sensitivities = Column(String(255), nullable=True)
    
    # created_at: Tracks when they took the quiz so we can show them their "taken on" date.
    created_at   = Column(DateTime, server_default=func.now())