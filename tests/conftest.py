import sys
import os
import pytest
from fastapi.testclient import TestClient

# Add the project root to the Python path
# This allows `from app.main import app` to work
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, PROJECT_ROOT)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.main import app  # Import your FastAPI app
from app.database import Base, get_db, create_db_and_tables
import os

# Use an in-memory SQLite database for testing
TEST_SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="session")
def db_engine():
    """Yields a SQLAlchemy engine for the test database."""
    engine = create_engine(
        TEST_SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine) # Create tables
    yield engine
    # Optionally, clean up by dropping tables, though for :memory: it's not strictly needed
    # Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db_session(db_engine):
    """Yields a SQLAlchemy session for a test. Manages transactions and rollback."""
    connection = db_engine.connect()

    # begin a non-ORM transaction
    trans = connection.begin()

    # bind an individual Session to the connection
    SessionLocal_test = sessionmaker(autocommit=False, autoflush=False, bind=connection)
    db = SessionLocal_test()

    yield db

    db.close()
    trans.rollback()
    connection.close()

@pytest.fixture(scope="function")
def client(db_session):
    """
    A TestClient fixture that uses the test database session.
    """

    def override_get_db():
        try:
            yield db_session
        finally:
            db_session.close()

    app.dependency_overrides[get_db] = override_get_db

    # Create all tables in the in-memory database before tests run.
    # This is done here to ensure tables are ready for each test function,
    # especially if tests might modify the schema or if using function-scoped engine.
    # If db_engine is session-scoped and tables are created there, this might be redundant
    # unless tests alter tables. For :memory: db, tables need to be created per connection/engine instance.
    # Re-creating engine and tables for each test via a function-scoped fixture might be safer for isolation.

    # The create_db_and_tables function in database.py might rely on the global 'engine'
    # For testing, we want to ensure it uses the test engine.
    # We've already created tables with Base.metadata.create_all(bind=db_engine) in db_engine fixture.
    # If create_db_and_tables is essential for setup beyond table creation, ensure it uses the test engine.

    with TestClient(app) as c:
        yield c

    # Clean up dependency overrides
    app.dependency_overrides.clear()
