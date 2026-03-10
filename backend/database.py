import os
import re  # Regular Expressions, used here to clean up the database URL string
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import NullPool  # Important for stable cloud deployments
from dotenv import load_dotenv

# 1. Load environment variables (like your DB password) from the .env file into Python's memory
load_dotenv()

# 2. Fetch the database connection string from the environment.
# Typically looks like: mysql://user:password@host:port/database_name
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "")

# 3. THE DRIVER FIX FOR CLOUD DATABASES
# Many cloud providers give a generic URL starting with "mysql://".
# However, SQLAlchemy needs to know EXACTLY which Python library (driver) to use to talk to MySQL.
# We replace "mysql://" with "mysql+pymysql://" to explicitly tell it to use the PyMySQL driver.
if SQLALCHEMY_DATABASE_URL.startswith("mysql://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("mysql://", "mysql+pymysql://", 1)

# 4. PREVENTING SSL CONFLICTS
# Some cloud URLs come with an automatic "?ssl-mode=REQUIRED" at the end.
# Because we are about to configure SSL manually in step 5, having it in the URL too 
# causes a "Duplicate Argument" crash. This Regex removes it from the URL string.
SQLALCHEMY_DATABASE_URL = re.sub(r'[?&]ssl[_-]mode=\w+', '', SQLALCHEMY_DATABASE_URL)

# 5. CREATE THE ENGINE (The actual connection manager)
# The engine is the core of SQLAlchemy. It manages the actual physical connection to the database.
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    
    # 6. SSL CONFIGURATION (Critical for Cloud MySQL)
    # This tells Python: "Connect securely via SSL, but don't strictly verify the 
    # server's certificate." This is required for many free-tier cloud databases 
    # that use self-signed certificates.
    connect_args={
        "ssl": {
            "check_hostname": False,
            "verify_mode": 0  # 0 means CERT_NONE (Do not strictly verify Certificate Authority)
        }
    },
    
    # 7. CONNECTION POOLING (Critical for Stability)
    # Normally, databases keep connections "open" to reuse them (Pooling). 
    # But in cheap/free cloud hosting, firewalls randomly kill idle connections, 
    # leading to the dreaded "MySQL server has gone away" error.
    # NullPool disables pooling entirely. It forces the app to open a brand-new 
    # connection for every single request and close it immediately after.
    poolclass=NullPool  
)



# 8. CREATE THE SESSION FACTORY
# A "Session" is a temporary workspace where you make your database queries.
# This 'SessionLocal' is a factory that creates a new workspace whenever we ask for one.
# autocommit=False ensures data isn't saved until we explicitly say db.commit().
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 9. THE BASE MODEL
# All your database tables (like the 'Ingredient' class) will inherit from this Base.
# It helps SQLAlchemy map your Python classes to actual SQL tables.
Base = declarative_base()

# 10. THE FASTAPI DEPENDENCY (The 'Middleman')
# Every time a user requests an API route, FastAPI runs this function.
def get_db():
    db = SessionLocal()  # Open a fresh database session
    try:
        yield db         # "Yield" hands the session over to the API route to do its work
    finally:
        db.close()       # CRITICAL: Always close the connection when the request finishes, 
                         # even if the code crashes! This prevents memory leaks.