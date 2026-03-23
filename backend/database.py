# 'os' is used to read environment variables from your operating system
import os

# 're' is Python's Regular Expression module. It's used here to search and replace text patterns in the database URL.
import re  

# Import the core tools from SQLAlchemy needed to connect to and communicate with the database
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# NullPool is a special setting that tells SQLAlchemy NOT to keep a pool of idle database connections open.
from sqlalchemy.pool import NullPool  

# Loads variables from a local '.env' file into the environment so 'os.getenv' can find them.
from dotenv import load_dotenv

load_dotenv()

# ==========================================
# 1. DATABASE URL FORMATTING
# ==========================================

# Fetches your raw database connection string. If it's not found, it defaults to an empty string to prevent instant crashes.
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "")

# SQLAlchemy requires both the database type (mysql) AND the driver being used to connect to it (pymysql).
# Many cloud database providers just give you "mysql://...". This line automatically fixes the URL 
# so SQLAlchemy knows exactly which Python driver to use.
if SQLALCHEMY_DATABASE_URL.startswith("mysql://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("mysql://", "mysql+pymysql://", 1)

# Cloud databases often append strict SSL requirements (like "?ssl-mode=STRICT") to the URL.
# This regex searches the URL for anything matching "ssl_mode=" or "ssl-mode=" and deletes it.
# We do this because we are going to manually configure the SSL settings in the create_engine block below.
SQLALCHEMY_DATABASE_URL = re.sub(r'[?&]ssl[_-]mode=\w+', '', SQLALCHEMY_DATABASE_URL)


# ==========================================
# 2. ENGINE CREATION (The Core Connection)
# ==========================================
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    
    # connect_args are extra parameters passed directly to the underlying pymysql driver.
    connect_args={
        # This dictionary lowers the strictness of the SSL connection. 
        # By setting check_hostname to False and verify_mode to 0 (CERT_NONE), 
        # we tell the driver to encrypt the traffic, but NOT to reject the connection 
        # if the database's SSL certificate is self-signed or missing a hostname match.
        "ssl": {
            "check_hostname": False,
            "verify_mode": 0  
        }
    },
    
    # By default, SQLAlchemy keeps 5-10 database connections open and idly waiting (a "pool").
    # NullPool disables this. Every time a user requests data, a fresh connection is opened, 
    # and when the request finishes, the connection is immediately destroyed. 
    # This is crucial for serverless deployments to prevent exhausting your database's connection limits.
    poolclass=NullPool  
)

# ==========================================
# 3. SESSION & ORM SETUP
# ==========================================

# SessionLocal is a "factory" that manufactures new, temporary database sessions.
# autocommit=False: We must manually call db.commit() to save changes, preventing accidental half-saves.
# autoflush=False: Prevents SQLAlchemy from prematurely pushing changes to the database before we are ready.
# bind=engine: Connects these sessions to the engine we configured above.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base is the foundational Python class that all your database models (like the User table) will inherit from.
# It tells SQLAlchemy how to map your Python code to actual SQL tables.
Base = declarative_base()


# ==========================================
# 4. DEPENDENCY INJECTION
# ==========================================
def get_db():
    """
    This is a FastAPI dependency. When a user hits a route (like logging in), 
    FastAPI calls this function to get a fresh database connection.
    """
    db = SessionLocal() 
    try:
        # 'yield' hands the active database connection to the FastAPI route that requested it.
        yield db       
    finally:
        # Once the FastAPI route finishes processing and returns a response to the user,
        # this block executes and securely closes the database connection.
        db.close()