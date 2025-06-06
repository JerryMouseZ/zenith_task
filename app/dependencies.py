# FastAPI dependencies (e.g., for authentication)
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError
from . import crud, models, schemas # Adjusted to use relative imports
from .core.security import decode_access_token # Adjusted to use relative imports
from .database import SessionLocal # Adjusted to use relative imports

# Database Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# OAuth2 Scheme
# The tokenUrl should point to your token generation endpoint, typically prefixed with /api
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

async def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> models.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    token_data = decode_access_token(token) # decode_access_token now returns schemas.TokenData or None
    if token_data is None or token_data.username is None:
        raise credentials_exception

    user = crud.get_user_by_username(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(
    current_user: models.User = Depends(get_current_user)
) -> models.User:
    if not current_user.is_active: # Ensure user is active
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")
    return current_user

# Example of a role-based dependency (conceptual)
# def require_admin_user(current_user: models.User = Depends(get_current_active_user)):
#     if not current_user.is_superuser: # Assuming User model has 'is_superuser'
#         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User does not have admin privileges")
#     return current_user
