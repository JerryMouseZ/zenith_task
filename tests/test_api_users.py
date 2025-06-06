import pytest
from fastapi.testclient import TestClient
from app import schemas # For input data and response validation
import time

# Helper to get a valid token
def get_auth_token(client: TestClient, email, password) -> str:
    response = client.post("/api/auth/token", data={"username": email, "password": password})
    if response.status_code == 200:
        return response.json()["access_token"]
    return ""

# --- User API Test Data & Setup ---
# Use unique data for registration in each test function or test class
# to avoid conflicts if tests are run multiple times or in parallel.

def generate_unique_user_data(base_username="testmeuser"):
    unique_suffix = time.time_ns()
    return {
        "email": f"{base_username}{unique_suffix}@example.com",
        "username": f"{base_username}{unique_suffix}",
        "password": "testmepassword",
    }

# --- User API Tests (/api/users/me) ---

def test_read_current_user_me(client: TestClient):
    user_data = generate_unique_user_data("readme")
    # Register user first
    reg_response = client.post("/api/auth/register", json=user_data)
    assert reg_response.status_code == 201

    # Login to get token
    token = get_auth_token(client, user_data["email"], user_data["password"])
    assert token != ""
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/api/users/me", headers=headers)
    if response.status_code != 200:
        print("Read current user /me failed:", response.json())
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == user_data["email"]
    assert data["username"] == user_data["username"]
    assert "id" in data

    # Test without token
    response_no_token = client.get("/api/users/me")
    assert response_no_token.status_code == 401 # Unauthorized

def test_update_current_user_me(client: TestClient):
    user_data = generate_unique_user_data("updateme")
    reg_response = client.post("/api/auth/register", json=user_data)
    assert reg_response.status_code == 201

    token = get_auth_token(client, user_data["email"], user_data["password"])
    assert token != ""
    headers = {"Authorization": f"Bearer {token}"}

    # Keep original username for the first update to ensure token remains valid
    original_username = user_data["username"]
    update_payload = {
        "email": f"updatedme{time.time_ns()}@example.com", # Ensure updated email is unique too
        "username": original_username, # Keep username same for first update
        # "is_active": False, # Keep user active for subsequent tests with same token
        "preferences": {"theme": "dark_updated"}
    }
    response = client.put("/api/users/me", json=update_payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == update_payload["email"]
    assert data["username"] == original_username # Check it's the original username
    # assert data["is_active"] is False # User should remain active
    assert data["is_active"] is True # Default User.is_active is True and we are not changing it.
    assert data["preferences"] == update_payload["preferences"]

    # Test partial update (e.g. only preferences)
    # Username is kept as original_username from the first update_payload.
    # Email is kept as update_payload["email"] from the first update.
    partial_update_payload = {"preferences": {"theme": "light_mode"}}
    response_partial = client.put("/api/users/me", json=partial_update_payload, headers=headers)
    assert response_partial.status_code == 200
    data_partial = response_partial.json()
    assert data_partial["username"] == original_username # Should remain original username
    assert data_partial["email"] == update_payload["email"] # Should remain from first update
    assert data_partial["preferences"] == partial_update_payload["preferences"]

    # Test updating email to one that's already taken by another user
    other_user_data = generate_unique_user_data("otherforconflict")
    client.post("/api/auth/register", json=other_user_data)

    conflict_update_payload = {"email": other_user_data["email"]}
    response_conflict = client.put("/api/users/me", json=conflict_update_payload, headers=headers)
    assert response_conflict.status_code == 400


def test_update_current_user_password(client: TestClient):
    user_data = generate_unique_user_data("passupdateme")
    reg_response = client.post("/api/auth/register", json=user_data)
    assert reg_response.status_code == 201

    token = get_auth_token(client, user_data["email"], user_data["password"])
    assert token != ""
    headers = {"Authorization": f"Bearer {token}"}

    new_password = "newstrongpassword123"
    password_update_payload = {
        "current_password": user_data["password"],
        "new_password": new_password
    }
    response = client.put("/api/users/me/password", json=password_update_payload, headers=headers)
    assert response.status_code == 204

    # Verify new password works for login
    new_token = get_auth_token(client, user_data["email"], new_password)
    assert new_token != ""

    # Verify old password no longer works
    old_token_fail = get_auth_token(client, user_data["email"], user_data["password"])
    assert old_token_fail == ""

    # Test with incorrect current_password
    incorrect_password_payload = {
        "current_password": "wrongoldpassword",
        "new_password": "anothernewpassword"
    }
    response_fail = client.put("/api/users/me/password", json=incorrect_password_payload, headers=headers)
    assert response_fail.status_code == 400


def test_user_preferences(client: TestClient):
    user_data = generate_unique_user_data("prefme")
    reg_response = client.post("/api/auth/register", json=user_data)
    assert reg_response.status_code == 201

    token = get_auth_token(client, user_data["email"], user_data["password"])
    assert token != ""
    headers = {"Authorization": f"Bearer {token}"}

    response_get_initial = client.get("/api/users/me/preferences", headers=headers)
    assert response_get_initial.status_code == 200
    initial_prefs = response_get_initial.json()
    assert initial_prefs == {} # Default for User model's JSON preferences is None/null, router returns {}

    prefs_payload = {"theme": "solarized", "notifications_enabled": False}
    response_put = client.put("/api/users/me/preferences", json=prefs_payload, headers=headers)
    assert response_put.status_code == 200
    updated_prefs_put = response_put.json()
    assert updated_prefs_put == prefs_payload

    response_get_updated = client.get("/api/users/me/preferences", headers=headers)
    assert response_get_updated.status_code == 200
    final_prefs = response_get_updated.json()
    assert final_prefs == prefs_payload

# Note: /api/users/ (GET all users) and /api/users/{user_id} (GET user by ID) are typically admin-only.
# Tests for these would require an admin user setup and token.
# For now, focusing on /me endpoints as per common user functionality.
