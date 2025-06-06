import pytest
from fastapi.testclient import TestClient
from app import schemas # For input data and response validation
import time

# Helper to generate unique user data for registration
def generate_unique_user_data(base_username="projectapiuser"):
    unique_suffix = time.time_ns()
    return {
        "email": f"{base_username}{unique_suffix}@example.com",
        "username": f"{base_username}{unique_suffix}",
        "password": "testpassword123",
    }

# Helper to get a valid token for a new user
def register_and_get_token(client: TestClient, base_username="projecttestuser") -> str:
    user_data = generate_unique_user_data(base_username)
    # Register user
    reg_response = client.post("/api/auth/register", json=user_data)
    assert reg_response.status_code == 201 # Assuming registration returns 201

    # Login to get token
    login_payload = {"username": user_data["email"], "password": user_data["password"]}
    token_response = client.post("/api/auth/token", data=login_payload)
    assert token_response.status_code == 200
    return token_response.json()["access_token"]

# --- Project API Test Data ---
PROJECT_CREATE_DATA_1 = {
    "name": "My First API Project",
    "description": "This is a project created via API tests.",
}

PROJECT_CREATE_DATA_2 = {
    "name": "Archived API Project",
    "description": "This project will be archived.",
    "is_archived": True
}


# --- Project API Tests (/api/projects) ---

def test_create_project(client: TestClient):
    token = register_and_get_token(client, "createprojectuser")
    headers = {"Authorization": f"Bearer {token}"}

    # Create a standard project
    response = client.post("/api/projects/", json=PROJECT_CREATE_DATA_1, headers=headers)
    assert response.status_code == 201 # As per api.md
    data = response.json()
    assert data["name"] == PROJECT_CREATE_DATA_1["name"]
    assert data["description"] == PROJECT_CREATE_DATA_1["description"]
    assert "id" in data
    assert data["is_archived"] is False # Default
    project_id_1 = data["id"]

    # Create an archived project
    response_archived = client.post("/api/projects/", json=PROJECT_CREATE_DATA_2, headers=headers)
    assert response_archived.status_code == 201
    data_archived = response_archived.json()
    assert data_archived["name"] == PROJECT_CREATE_DATA_2["name"]
    assert data_archived["is_archived"] is True
    assert data_archived["archived_at"] is not None # Should be set by CRUD

    # Test creating project with missing required fields (e.g., name)
    response_missing_name = client.post("/api/projects/", json={"description": "no name"}, headers=headers)
    assert response_missing_name.status_code == 422 # Unprocessable Entity

def test_get_projects(client: TestClient):
    token_user1 = register_and_get_token(client, "getprojectsuser1")
    headers_user1 = {"Authorization": f"Bearer {token_user1}"}

    # User 1 creates two projects
    client.post("/api/projects/", json={"name": "U1 Project 1 (Active)"}, headers=headers_user1)
    client.post("/api/projects/", json={"name": "U1 Project 2 (Archived)", "is_archived": True}, headers=headers_user1)

    token_user2 = register_and_get_token(client, "getprojectsuser2")
    headers_user2 = {"Authorization": f"Bearer {token_user2}"}
    # User 2 creates one project
    client.post("/api/projects/", json={"name": "U2 Project 1 (Active)"}, headers=headers_user2)

    # Get active projects for User 1 (assuming router default archived=False as per api.md)
    response_user1_active_default = client.get("/api/projects/", headers=headers_user1)
    assert response_user1_active_default.status_code == 200
    projects_user1_active_default = response_user1_active_default.json()
    assert len(projects_user1_active_default) == 1
    assert projects_user1_active_default[0]["name"] == "U1 Project 1 (Active)"

    # Get active projects for User 1 (explicitly)
    response_user1_active = client.get("/api/projects/?archived=false", headers=headers_user1)
    assert response_user1_active.status_code == 200
    projects_user1_active = response_user1_active.json()
    assert len(projects_user1_active) == 1
    assert projects_user1_active[0]["name"] == "U1 Project 1 (Active)"

    # Get archived projects for User 1
    response_user1_archived = client.get("/api/projects/?archived=true", headers=headers_user1)
    assert response_user1_archived.status_code == 200
    projects_user1_archived = response_user1_archived.json()
    assert len(projects_user1_archived) == 1
    assert projects_user1_archived[0]["name"] == "U1 Project 2 (Archived)"

    # Get all projects for User 1 (by explicitly setting archived to None or a value not 'true'/'false' if router handles it, or if no param means all)
    # This depends on router interpretation. For now, assume no param means default (active as per api.md)
    # To test "all", the API would need a way to specify this, e.g. /api/projects/?archived=all or similar.
    # Or, if the router's Optional[bool] defaults to None in CRUD, and CRUD's None means all.
    # Based on `crud.get_projects_by_user archived: Optional[bool] = None`, if router passes None, it's all.
    # If router's `archived: Optional[bool] = False` (FastAPI default for Optional[bool] Query is None unless default_factory or default is set)
    # then if `archived` param is omitted, `archived` in router is `False`.
    # Let's assume for now the router default for the query param makes it `False` if omitted.

    # Get projects for User 2 (should only see their own active one by default)
    response_user2 = client.get("/api/projects/", headers=headers_user2)
    assert response_user2.status_code == 200
    projects_user2 = response_user2.json()
    assert len(projects_user2) == 1
    assert projects_user2[0]["name"] == "U2 Project 1 (Active)"

    # Test without token
    response_no_token = client.get("/api/projects/")
    assert response_no_token.status_code == 401

def test_get_project_by_id(client: TestClient):
    token = register_and_get_token(client, "getprojectbyiduser")
    headers = {"Authorization": f"Bearer {token}"}

    create_response = client.post("/api/projects/", json=PROJECT_CREATE_DATA_1, headers=headers)
    assert create_response.status_code == 201
    project_id = create_response.json()["id"]

    response = client.get(f"/api/projects/{project_id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == project_id
    assert data["name"] == PROJECT_CREATE_DATA_1["name"]

    # Test getting non-existent project
    response_not_found = client.get(f"/api/projects/99999", headers=headers)
    assert response_not_found.status_code == 404

    # Test getting project not owned by user
    token_other_user = register_and_get_token(client, "othergetprojectuser")
    headers_other_user = {"Authorization": f"Bearer {token_other_user}"}
    response_forbidden = client.get(f"/api/projects/{project_id}", headers=headers_other_user)
    assert response_forbidden.status_code == 404

def test_update_project(client: TestClient):
    token = register_and_get_token(client, "updateprojectuser")
    headers = {"Authorization": f"Bearer {token}"}

    create_response = client.post("/api/projects/", json=PROJECT_CREATE_DATA_1, headers=headers)
    assert create_response.status_code == 201
    project_id = create_response.json()["id"]

    update_payload = {
        "name": "Updated API Project Name",
        "description": "This project has been updated.",
        "is_archived": True
    }
    response = client.put(f"/api/projects/{project_id}", json=update_payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == project_id
    assert data["name"] == update_payload["name"]
    assert data["description"] == update_payload["description"]
    assert data["is_archived"] is True
    assert data["archived_at"] is not None

    # Test updating project not owned by user
    token_other_user = register_and_get_token(client, "otherupdateprojectuser")
    headers_other_user = {"Authorization": f"Bearer {token_other_user}"}
    response_forbidden = client.put(f"/api/projects/{project_id}", json=update_payload, headers=headers_other_user)
    assert response_forbidden.status_code == 404

    # Test partial update
    partial_payload = {"name": "Super Updated Name"}
    response_partial = client.put(f"/api/projects/{project_id}", json=partial_payload, headers=headers)
    assert response_partial.status_code == 200
    data_partial = response_partial.json()
    assert data_partial["name"] == "Super Updated Name"
    assert data_partial["description"] == update_payload["description"] # Should remain
    assert data_partial["is_archived"] is True # Should remain

def test_delete_project(client: TestClient):
    token = register_and_get_token(client, "deleteprojectuser")
    headers = {"Authorization": f"Bearer {token}"}

    # Create a project to delete
    project_to_delete_name = f"ProjectToDelete_{time.time_ns()}"
    create_response = client.post("/api/projects/", json={"name": project_to_delete_name, "description":"To be deleted"}, headers=headers)
    assert create_response.status_code == 201
    project_id_to_delete = create_response.json()["id"]

    # Delete the project
    response = client.delete(f"/api/projects/{project_id_to_delete}", headers=headers)
    assert response.status_code == 204

    # Verify project is deleted
    get_response = client.get(f"/api/projects/{project_id_to_delete}", headers=headers)
    assert get_response.status_code == 404

    # Test deleting non-existent project
    response_not_found = client.delete(f"/api/projects/99999", headers=headers)
    assert response_not_found.status_code == 404

    # Test attempting to delete project owned by another user
    # 1. User1 creates a project
    project_to_keep_name = f"ProjectToKeep_{time.time_ns()}"
    new_create_resp = client.post("/api/projects/", json={"name": project_to_keep_name}, headers=headers)
    assert new_create_resp.status_code == 201
    project_id_to_keep = new_create_resp.json()["id"]

    # 2. User2 tries to delete it
    token_other_user = register_and_get_token(client, "otherdeleteprojectuser")
    headers_other_user = {"Authorization": f"Bearer {token_other_user}"}
    response_forbidden = client.delete(f"/api/projects/{project_id_to_keep}", headers=headers_other_user)
    assert response_forbidden.status_code == 404

    # Verify project still exists for User1
    get_response_user1 = client.get(f"/api/projects/{project_id_to_keep}", headers=headers)
    assert get_response_user1.status_code == 200
    assert get_response_user1.json()["name"] == project_to_keep_name
