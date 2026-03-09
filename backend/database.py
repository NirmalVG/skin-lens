import os
import re # Regular Expressions, used to clean up the URL string
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import NullPool # Important for cloud deployment
from dotenv import load_dotenv

# 1. Load secrets (DB password, etc.) from the .env file into Python's memory
load_dotenv()

# 2. Get the connection string (URL) from the environment
# It looks like: mysql://user:password@host:port/database_name
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "")

# 3. FIX FOR CLOUD PROVIDERS (The "Driver" Hack)
# Many cloud providers give a URL starting with "mysql://".
# SQLAlchemy needs to know WHICH driver to use. We force it to use "pymysql".
if SQLALCHEMY_DATABASE_URL.startswith("mysql://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("mysql://", "mysql+pymysql://", 1)

# 4. REMOVE SSL PARAMETERS FROM URL
# Sometimes the URL comes with "?ssl-mode=REQUIRED". We remove this because
# we are going to configure SSL manually in the 'connect_args' below.
# This prevents a "Duplicate Argument" error.
SQLALCHEMY_DATABASE_URL = re.sub(r'[?&]ssl[_-]mode=\w+', '', SQLALCHEMY_DATABASE_URL)

# 5. CREATE THE ENGINE (The actual connection starter)
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    
    # SSL CONFIGURATION (Critical for Render/Aiven/PlanetScale)
    # This tells Python: "Connect securely, but don't panic if the 
    # server's certificate looks a bit weird (self-signed)."
    connect_args={
        "ssl": {
            "check_hostname": False,
            "verify_mode": 0  # 0 means CERT_NONE (Don't verify CA)
        }
    },
    
    # CONNECTION POOLING (Critical for Stability)
    # By default, SQLAlchemy keeps connections open to reuse them (Pooling).
    # On cheap cloud hosting, open connections get cut off, causing "Server has gone away" errors.
    # NullPool disables this, forcing a fresh connection for every request. Slower, but much safer.
    poolclass=NullPool  
)

# 6. CREATE THE SESSION FACTORY
# This is a tool that creates a new "Session" (a temporary workspace) for every request.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 7. CREATE THE BASE CLASS
# All your models (Ingredient, User, etc.) will inherit from this class.
# It helps SQLAlchemy track which tables belong to your app.
Base = declarative_base()

# 8. THE DEPENDENCY INJECTION FUNCTION
# FastAPI uses this to give every API route a database session.
def get_db():
    db = SessionLocal() # Open a new session
    try:
        yield db # Pass the session to the API route to do work
    finally:
        db.close() # CRITICAL: Always close the session when done, even if the code crashes.