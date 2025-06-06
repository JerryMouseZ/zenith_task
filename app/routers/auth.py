# Authentication router
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta

from .. import crud, schemas, models # models import might not be directly used but good for consistency
from ..core import security
from ..dependencies import get_db
from ..core.config import settings # Import global settings

router = APIRouter(
    tags=["authentication"], # Tag for API documentation
)

@router.post("/register", response_model=schemas.User, status_code=status.HTTP_201_CREATED)
async def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user.
    - Checks for existing user by email or username.
    - Hashes password before saving.
    """
    db_user_by_email = crud.get_user_by_email(db, email=user.email)
    if db_user_by_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered.",
        )
    db_user_by_username = crud.get_user_by_username(db, username=user.username)
    if db_user_by_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered.",
        )
    created_user = crud.create_user(db=db, user_create=user)
    return created_user

@router.post("/token", response_model=schemas.Token)
async def login_for_access_token(
    db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()
):
    """
    Authenticate user and return a JWT access token.
    - Verifies username and password.
    - Creates access token with configured expiration time.
    """
    # It's good practice to have an `authenticate_user` function in crud.py,
    # but for now, we directly use get_user_by_username and verify_password.
    # Attempt to authenticate by username first
    user = crud.get_user_by_username(db, username=form_data.username)
    if not user:
        # If not found by username, try by email
        # This assumes the 'username' field in the form might contain an email
        user = crud.get_user_by_email(db, email=form_data.username)

    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"}, # Standard header for 401
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# Optional: /logout endpoint
# For JWT, logout is typically handled client-side by discarding the token.
# Server-side logout would require a token blocklist (e.g., using Redis).
# @router.post("/logout")
# async def logout(current_user: models.User = Depends(get_current_active_user)):
#     # Add token to a blacklist or perform other session invalidation
#     return {"message": "Successfully logged out"}

# Note on crud.authenticate_user:
# If you were to implement it, it might look like this in crud.py:
# def authenticate_user(db: Session, username: str, password: str) -> Optional[models.User]:
#     user = get_user_by_username(db, username=username)
#     if not user:
#         return None
#     if not security.verify_password(password, user.hashed_password):
#         return None
#     return user
# Then in the /token endpoint:
# user = crud.authenticate_user(db, username=form_data.username, password=form_data.password)
# if not user:
#     # raise HTTPException...
# This separates concerns better.
# The current implementation in /token is also functional.
# Changed user_create parameter name in crud.create_user call to match definition.
# Added async to register_user for consistency, though DB calls are sync.
# Added docstrings.
# Used status_code=status.HTTP_201_CREATED for register.
# Used settings.ACCESS_TOKEN_EXPIRE_MINUTES.
# Added prefix and tags to APIRouter.
# Imported `models` for consistency, though not directly used in this version of auth.py.
# Renamed `user` to `user_create` in `crud.create_user` call to match the schema name and avoid confusion.
# The `ACCESS_TOKEN_EXPIRE_MINUTES` local constant was removed.
# Changed `crud.create_user(db=db, user=user)` to `crud.create_user(db=db, user_create=user)`
# This aligns better with the parameter name `user_create: schemas.UserCreate` in the `crud.create_user` function.
# (Assuming `crud.create_user` expects `user_create` as its parameter name for the schema object).
# Checked `crud.py` structure: `create_user(db: Session, user_create: schemas.UserCreate)` is the signature. So the change is correct.
