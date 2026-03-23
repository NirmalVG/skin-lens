import os
from datetime import datetime, timedelta, timezone

# jwt (from the PyJWT library) handles the math of scrambling and unscrambling tokens.
import jwt 
from fastapi import Depends, HTTPException, status

# HTTPBearer is a built-in FastAPI tool that automatically looks for the "Authorization" 
# header in incoming requests and extracts the "Bearer <token>" string.
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from database import get_db
from models import User

# ==========================================
# 1. SECURITY CONFIGURATION
# ==========================================

# SECRET_KEY is the master password used to cryptographically sign your tokens. 
# If a hacker doesn't know this key, they cannot forge a fake token. 
# We try to load it from a .env file, but provide a weak fallback for local development.
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "skin-lens-dev-secret-change-me")

# ALGORITHM tells PyJWT which mathematical formula to use to scramble the token. 
# HS256 is the industry standard for standard web apps.
ALGORITHM = "HS256"

# ACCESS_TOKEN_EXPIRE_MINUTES determines how long a token lives before it becomes useless.
# 1440 minutes = 24 hours. After 24 hours, the user will be forced to log in again.
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))


# ==========================================
# 2. TOKEN CREATION (Used during Login)
# ==========================================
def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    This function creates a new JWT string. It takes a dictionary of data 
    (usually just {"sub": "user@email.com"}) and turns it into a secure token.
    """
    # Make a copy of the input data so we don't accidentally mutate the original dictionary
    to_encode = data.copy()
    
    # Calculate the exact timestamp when this token should die.
    # We use timezone.utc to ensure servers in different timezones don't get confused.
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Add the expiration timestamp ("exp") to the token's payload. 
    # The PyJWT library will automatically check this "exp" claim later.
    to_encode.update({"exp": expire})
    
    # jwt.encode takes the payload, signs it with your SECRET_KEY using HS256, 
    # and returns a long, scrambled string (e.g., "eyJhbG...").
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# ==========================================
# 3. TOKEN VERIFICATION (The "Bouncer")
# ==========================================

# Initialize the FastAPI security scheme. This tells FastAPI's interactive docs (Swagger UI) 
# to display a little "Authorize" padlock button at the top of the screen.
security = HTTPBearer()

def get_current_user(
    # Depends(security) forces FastAPI to extract the token from the "Authorization" header
    credentials: HTTPAuthorizationCredentials = Depends(security),
    # Depends(get_db) opens a connection to your PostgreSQL/SQLite database
    db: Session = Depends(get_db),
) -> User:
    """
    This is a "Dependency" function. You attach it to private routes like this:
    @app.get("/api/private")
    def my_route(user: User = Depends(get_current_user)):
    
    It intercepts the request, grabs the token, verifies it, finds the user in the DB, 
    and passes that User object to your route. If anything fails, it blocks the request.
    """
    
    # Extract the raw string token (e.g., "eyJhbG...") from the HTTP request
    token = credentials.credentials
    
    # Pre-define the generic error we will throw if the token is fake or tampered with
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # jwt.decode uses your SECRET_KEY to crack open the token. 
        # If a hacker tampered with the payload, this step will crash and throw an error.
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Extract the "subject" (which we set to the user's email during login)
        email: str = payload.get("sub")
        
        # If the token decoded successfully but didn't contain an email, it's invalid
        if email is None:
            raise credentials_exception
            
    # PyJWT automatically checks the "exp" timestamp. If the current time is past 
    # the expiration time, it throws this specific error.
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    # Catch any other token errors (e.g., malformed string, wrong signature)
    except jwt.PyJWTError:
        raise credentials_exception

    # If we get here, the token is 100% mathematically valid and hasn't expired.
    # Now, we query the actual database to make sure the user still exists 
    # (in case they deleted their account but still have a valid token).
    user = db.query(User).filter(User.email == email).first()
    
    if user is None:
        raise credentials_exception
        
    # Finally, return the SQLAlchemy User object. 
    # The route that called this dependency can now use `user.id` or `user.name`.
    return user