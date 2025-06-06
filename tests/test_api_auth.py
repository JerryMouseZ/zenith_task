import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session # To verify DB state if needed
from app import crud, schemas # For input data and response validation
import time # For unique data generation

# Helper to generate unique user data for tests
def generate_auth_test_user_data(base_username="authtestuser"):
    unique_suffix = time.time_ns()
    return {
        "email": f"{base_username}{unique_suffix}@example.com",
        "username": f"{base_username}{unique_suffix}",
        "password": "testpassword",
    }

# --- Auth API Tests ---

def test_app_root(client: TestClient):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to ZenithTask API. Navigate to /docs for API documentation."}

def test_user_register(client: TestClient, db_session: Session):
    user_data = generate_auth_test_user_data("register")

    response = client.post("/api/auth/register", json=user_data)
    if response.status_code != 201:
        print(f"Initial registration failed for {user_data['email']}: {response.json()}")
    assert response.status_code == 201

    data = response.json()
    assert data["email"] == user_data["email"]
    assert data["username"] == user_data["username"]
    assert "id" in data
    assert "hashed_password" not in data

    # Instead of direct DB check, try to login (which involves DB lookup via API)
    login_response = client.post("/api/auth/token", data={
        "username": user_data["email"],
        "password": user_data["password"]
    })
    if login_response.status_code != 200:
        # This will give us the detail from the /token endpoint if user not found by it
        print(f"Login attempt after registration failed for {user_data['email']}: {login_response.json()}")
    assert login_response.status_code == 200 # Verify user is effectively in DB by successful login

    # Test registering with existing email (using the same dynamically generated data)
    response_existing_email = client.post("/api/auth/register", json=user_data)
    assert response_existing_email.status_code == 400
    assert "Email already registered" in response_existing_email.json()["detail"]

def test_user_login_for_access_token(client: TestClient):
    user_data = generate_auth_test_user_data("login")

    # First, register a user to ensure the user exists for login
    register_response = client.post("/api/auth/register", json=user_data)
    if register_response.status_code != 201:
        print(f"Login pre-registration failed for {user_data['email']}: {register_response.json()}")
    assert register_response.status_code == 201

    login_response = client.post("/api/auth/token", data={
        "username": user_data["email"], # Login with email
        "password": user_data["password"]
    })
    assert login_response.status_code == 200
    token_data = login_response.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"

    # Test login with incorrect password
    login_fail_response = client.post("/api/auth/token", data={
        "username": user_data["email"], # Was unique_register_data, corrected to user_data
        "password": "wrongpassword"
    })
    assert login_fail_response.status_code == 401 # Unauthorized

    # Test login with non-existent user
    login_non_existent_response = client.post("/api/auth/token", data={
        "username": "nonexistent@example.com",
        "password": "anypassword"
    })
    assert login_non_existent_response.status_code == 401 # Unauthorized

# test_user_logout can be added if /api/auth/logout is implemented with server-side logic (e.g. token blacklisting)
# For now, assuming JWT is client-side deleted.
