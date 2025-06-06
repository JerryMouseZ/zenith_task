# Configuration settings
from pydantic import BaseSettings
import os

class Settings(BaseSettings):
    APP_NAME: str = "My FastAPI App"
    DEBUG_MODE: bool = False
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./sql_app.db")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "a_very_secret_key_that_should_be_changed")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Example for external service integration
    # EXTERNAL_API_KEY: Optional[str] = None
    # EXTERNAL_API_URL: Optional[str] = None

    # Email settings (example)
    # MAIL_USERNAME: Optional[str] = None
    # MAIL_PASSWORD: Optional[str] = None
    # MAIL_FROM: Optional[str] = None
    # MAIL_PORT: int = 587
    # MAIL_SERVER: Optional[str] = None
    # MAIL_TLS: bool = True
    # MAIL_SSL: bool = False

    class Config:
        # If you have a .env file, pydantic will load it.
        # Ensure `python-dotenv` is installed: pip install python-dotenv
        env_file = ".env"
        env_file_encoding = 'utf-8'

settings = Settings()

# You can print settings for debugging during startup, but be careful with sensitive data.
# print(f"Loaded settings: {settings.dict(exclude={'SECRET_KEY', 'DATABASE_URL'})}") # Exclude sensitive fields
from typing import Optional # Added this import to fix the error "name 'Optional' is not defined"
