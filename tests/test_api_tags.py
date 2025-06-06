import pytest
from fastapi.testclient import TestClient
from app import schemas # For input data and response validation
import time

# Helper to generate unique user data for registration
def generate_unique_user_data(base_username="tagapiuser"):
    unique_suffix = time.time_ns()
    return {
        "email": f"{base_username}{unique_suffix}@example.com",
        "username": f"{base_username}{unique_suffix}",
        "password": "testpassword123",
    }

# Helper to register a new user and get an auth token
def register_and_get_token(client: TestClient, base_username="tagtestuser") -> str:
    user_data = generate_unique_user_data(base_username)
    reg_response = client.post("/api/auth/register", json=user_data)
    assert reg_response.status_code == 201

    login_payload = {"username": user_data["email"], "password": user_data["password"]}
    token_response = client.post("/api/auth/token", data=login_payload)
    assert token_response.status_code == 200
    return token_response.json()["access_token"]

# --- Tag API Test Data ---
TAG_CREATE_DATA_1 = {
    "name": "API Tag Main",
    "color": "#123456",
}

TAG_CREATE_DATA_2 = {
    "name": "API Tag Secondary",
    "color": "#FEDCBA",
}

# --- Tag API Tests (/api/tags) ---

def test_create_tag(client: TestClient):
    token = register_and_get_token(client, "createtaguser")
    headers = {"Authorization": f"Bearer {token}"}

    # Create a tag
    unique_tag_name_1 = f"{TAG_CREATE_DATA_1['name']}_{time.time_ns()}"
    payload1 = {"name": unique_tag_name_1, "color": TAG_CREATE_DATA_1["color"]}
    response = client.post("/api/tags/", json=payload1, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == unique_tag_name_1
    assert data["color"] == TAG_CREATE_DATA_1["color"]
    assert "id" in data
    # tag_id_1 = data["id"] # Not used in this test directly

    # Test creating tag with the same name for the same user (should fail)
    response_duplicate = client.post("/api/tags/", json=payload1, headers=headers)
    # The router for POST /tags/ uses status_code=status.HTTP_400_BAD_REQUEST for ValueError (name collision)
    # and status_code=status.HTTP_409_CONFLICT for IntegrityError.
    # crud.create_tag raises ValueError: "Tag with this name already exists for this user."
    assert response_duplicate.status_code == 400
    assert "already exists" in response_duplicate.json()["detail"]


    # Test creating tag with missing required fields (e.g., name)
    response_missing_name = client.post("/api/tags/", json={"color": "#000000"}, headers=headers)
    assert response_missing_name.status_code == 422

def test_get_tags(client: TestClient):
    token_user1 = register_and_get_token(client, "gettagsuser1")
    headers_user1 = {"Authorization": f"Bearer {token_user1}"}

    # User 1 creates two tags
    # Ensure color codes are valid 6-digit hex
    client.post("/api/tags/", json={"name": f"U1 Tag 1 {time.time_ns()}", "color": "#AAAAAA"}, headers=headers_user1)
    client.post("/api/tags/", json={"name": f"U1 Tag 2 {time.time_ns()}", "color": "#BBBBBB"}, headers=headers_user1)

    token_user2 = register_and_get_token(client, "gettagsuser2")
    headers_user2 = {"Authorization": f"Bearer {token_user2}"}
    # User 2 creates one tag
    client.post("/api/tags/", json={"name": f"U2 Tag 1 {time.time_ns()}", "color": "#CCCCCC"}, headers=headers_user2)

    # Get all tags for User 1
    response_user1_all = client.get("/api/tags/", headers=headers_user1)
    assert response_user1_all.status_code == 200
    tags_user1_all = response_user1_all.json()
    assert len(tags_user1_all) == 2

    # Get tags for User 2 (should only see their own)
    response_user2 = client.get("/api/tags/", headers=headers_user2)
    assert response_user2.status_code == 200
    tags_user2 = response_user2.json()
    assert len(tags_user2) == 1
    assert tags_user2[0]["name"].startswith("U2 Tag 1")

    # Test without token
    response_no_token = client.get("/api/tags/")
    assert response_no_token.status_code == 401


def test_get_tag_by_id(client: TestClient):
    token = register_and_get_token(client, "gettagbyiduser")
    headers = {"Authorization": f"Bearer {token}"}

    unique_tag_name = f"{TAG_CREATE_DATA_1['name']}_ById_{time.time_ns()}"
    payload = {"name": unique_tag_name, "color": TAG_CREATE_DATA_1["color"]}
    create_response = client.post("/api/tags/", json=payload, headers=headers)
    assert create_response.status_code == 201
    tag_id = create_response.json()["id"]

    response = client.get(f"/api/tags/{tag_id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == tag_id
    assert data["name"] == unique_tag_name

    # Test getting non-existent tag
    response_not_found = client.get(f"/api/tags/999999", headers=headers)
    assert response_not_found.status_code == 404

    # Test getting tag not owned by user
    token_other_user = register_and_get_token(client, "othergettaguser")
    headers_other_user = {"Authorization": f"Bearer {token_other_user}"}
    response_forbidden = client.get(f"/api/tags/{tag_id}", headers=headers_other_user)
    assert response_forbidden.status_code == 404

def test_update_tag(client: TestClient):
    token = register_and_get_token(client, "updatetaguser")
    headers = {"Authorization": f"Bearer {token}"}

    original_name = f"Original API Tag_{time.time_ns()}"
    create_payload = {"name": original_name, "color": TAG_CREATE_DATA_1["color"]}
    create_response = client.post("/api/tags/", json=create_payload, headers=headers)
    assert create_response.status_code == 201
    tag_id = create_response.json()["id"]

    updated_name = f"Updated API Tag Name_{time.time_ns()}"
    update_payload = {
        "name": updated_name,
        "color": "#00FF00"
    }
    response = client.put(f"/api/tags/{tag_id}", json=update_payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == tag_id
    assert data["name"] == updated_name
    assert data["color"] == "#00FF00"

    # Test updating tag not owned by user
    token_other_user = register_and_get_token(client, "otherupdatetaguser")
    headers_other_user = {"Authorization": f"Bearer {token_other_user}"}
    response_forbidden = client.put(f"/api/tags/{tag_id}", json=update_payload, headers=headers_other_user)
    assert response_forbidden.status_code == 404

    # Test partial update (only color)
    partial_payload = {"color": "#112233"}
    response_partial = client.put(f"/api/tags/{tag_id}", json=partial_payload, headers=headers)
    assert response_partial.status_code == 200
    data_partial = response_partial.json()
    assert data_partial["name"] == updated_name
    assert data_partial["color"] == "#112233"

    # Test updating name to an existing tag name of the same user (should fail)
    existing_tag_payload = {"name": f"ExistingNameForUpdateFail_{time.time_ns()}", "color": "#CCCCCC"}
    client.post("/api/tags/", json=existing_tag_payload, headers=headers)

    fail_update_payload = {"name": existing_tag_payload["name"]}
    response_fail_update = client.put(f"/api/tags/{tag_id}", json=fail_update_payload, headers=headers)
    assert response_fail_update.status_code == 400

def test_delete_tag(client: TestClient):
    token = register_and_get_token(client, "deletetaguser")
    headers = {"Authorization": f"Bearer {token}"}

    delete_tag_name = f"TagToDelete_{time.time_ns()}"
    create_payload = {"name": delete_tag_name, "color": TAG_CREATE_DATA_1["color"]}
    create_response = client.post("/api/tags/", json=create_payload, headers=headers)
    assert create_response.status_code == 201
    tag_id = create_response.json()["id"]

    response = client.delete(f"/api/tags/{tag_id}", headers=headers)
    assert response.status_code == 204

    # Verify tag is deleted
    get_response = client.get(f"/api/tags/{tag_id}", headers=headers)
    assert get_response.status_code == 404

    # Test deleting non-existent tag
    response_not_found = client.delete(f"/api/tags/999999", headers=headers)
    assert response_not_found.status_code == 404

    # Test deleting tag not owned by user
    kept_tag_name = f"KeptTagByUser1_{time.time_ns()}"
    kept_tag_payload = {"name": kept_tag_name, "color": "#EEEEEE"}
    kept_tag_create_resp = client.post("/api/tags/", json=kept_tag_payload, headers=headers)
    assert kept_tag_create_resp.status_code == 201
    tag_id_to_keep = kept_tag_create_resp.json()["id"]

    token_other_user = register_and_get_token(client, "otherdeletetaguser")
    headers_other_user = {"Authorization": f"Bearer {token_other_user}"}
    response_forbidden = client.delete(f"/api/tags/{tag_id_to_keep}", headers=headers_other_user)
    assert response_forbidden.status_code == 404

    # Verify tag still exists for User1
    get_response_user1 = client.get(f"/api/tags/{tag_id_to_keep}", headers=headers)
    assert get_response_user1.status_code == 200
    assert get_response_user1.json()["name"] == kept_tag_name
