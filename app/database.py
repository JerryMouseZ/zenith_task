# Database connection and session management
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# Define the SQLite database URL
# For SQLite, `check_same_thread` is needed because SQLite by default only allows one thread to communicate with it,
# assuming that each thread would open its own database connection. FastAPI, being asynchronous, can have multiple
# threads interacting with the database in the same request, so this argument is necessary for SQLite.
# For other databases like PostgreSQL, you wouldn't need `connect_args={"check_same_thread": False}`.
SQLALCHEMY_DATABASE_URL = "sqlite:///./zenithtask.db"
# Example for PostgreSQL:
# SQLALCHEMY_DATABASE_URL = "postgresql://user:password@host:port/dbname"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}, # Only for SQLite
    # echo=True # Set to True to log all SQL statements issued by SQLAlchemy, useful for debugging
)

# Create a SessionLocal class for generating database sessions
# Each instance of SessionLocal will be a database session.
# autocommit=False and autoflush=False are standard settings for FastAPI.
# Operations are only committed when db.commit() is called.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a Base class for declarative models
# SQLAlchemy models will inherit from this class.
Base = declarative_base()

# Dependency to get a DB session per request
def get_db():
    """
    FastAPI dependency that provides a SQLAlchemy database session.
    It ensures the database session is always closed after the request.
    """
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_db_and_tables():
    """
    Creates all database tables defined by models inheriting from Base.
    This function should be called once on application startup.
    It checks for the existence of tables before creating them, so it's safe to call multiple times.
    """
    # In a real application, you might use Alembic for migrations instead of this.
    # This function is suitable for development and simple applications.
    print("Attempting to create database tables...")
    try:
        # The import of models here is crucial. SQLAlchemy's Base.metadata needs to be populated
        # with table definitions from your models before create_all is called.
        # If models are not imported, Base.metadata will be empty and no tables will be created.
        from . import models # This line ensures that all models are loaded by SQLAlchemy
        Base.metadata.create_all(bind=engine)
        print("Database tables created successfully (if they didn't exist already).")
    except Exception as e:
        print(f"Error creating database tables: {e}")
        # Consider raising the exception or handling it more robustly
        # depending on your application's startup error handling strategy.
        raise

# If you were to use Alembic for migrations, you would typically initialize it
# and manage database schema changes through migration scripts rather than calling
# Base.metadata.create_all() directly in your application code, especially for production.
# For example, you would have an `alembic.ini` file and a `migrations` directory.
# `create_db_and_tables` is fine for getting started or for simpler projects.
# Note: The `from . import models` inside `create_db_and_tables` is a common pattern
# to ensure that all model classes are registered with `Base.metadata` before `create_all` is called.
# This avoids circular import issues that might arise if models were imported at the top level
# and `models.py` also imported something from `database.py` (like `Base` itself).
# The current structure where `models.py` imports `Base` from `database.py` and `database.py`
# imports `models` inside a function is a good way to manage this.
