import pytest
from fastapi.testclient import TestClient
from app import schemas # For input data and response validation
import time
import datetime

# Helper to generate unique user data for registration
def generate_unique_user_data(base_username="taskapiuser"):
    unique_suffix = time.time_ns()
    return {
        "email": f"{base_username}{unique_suffix}@example.com",
        "username": f"{base_username}{unique_suffix}",
        "password": "testpassword123",
    }

# Helper to register a new user and get an auth token
def register_and_get_token(client: TestClient, base_username="tasktestuser") -> str:
    user_data = generate_unique_user_data(base_username)
    # Register user
    reg_response = client.post("/api/auth/register", json=user_data)
    assert reg_response.status_code == 201 # Assuming registration returns 201

    # Login to get token
    login_payload = {"username": user_data["email"], "password": user_data["password"]}
    token_response = client.post("/api/auth/token", data=login_payload)
    assert token_response.status_code == 200
    return token_response.json()["access_token"]

# Helper to create a project for a user
def create_project_for_user(client: TestClient, token: str, project_name_suffix="") -> int:
    project_data = {"name": f"Test Project for Tasks {project_name_suffix} {time.time_ns()}"}
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/api/projects/", json=project_data, headers=headers)
    assert response.status_code == 201
    return response.json()["id"]

# Helper to create a tag for a user
def create_tag_for_user(client: TestClient, token: str, tag_name_suffix="") -> int:
    tag_name = f"Test Tag for Tasks {tag_name_suffix} {time.time_ns()}"
    # Ensure tag name does not exceed max_length (50 for TagBase)
    if len(tag_name) > 50:
        tag_name = tag_name[:50] # Truncate, though this might lead to collisions if not careful
    tag_data = {"name": tag_name, "color": "#ABCDEF"}
    print(f"Creating tag with data: {tag_data}") # Debug print
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/api/tags/", json=tag_data, headers=headers)
    if response.status_code != 201:
        print(f"Create tag failed for '{tag_name}': {response.status_code} {response.text}")
    assert response.status_code == 201
    return response.json()["id"]


# --- Task API Test Data ---
TASK_CREATE_DATA_1 = {
    "title": "My First API Task",
    "description": "This task was created via API tests.",
    # project_id will be added dynamically
}

TASK_CREATE_DATA_2 = {
    "title": "Another API Task - High Priority",
    "description": "A second task, with more details.",
    "priority": 2, # High
    "completed": False,
    # due_date can be added: "due_date": "2024-12-31T23:59:59Z"
}

# --- Task API Tests (/api/tasks) ---

def test_create_task(client: TestClient):
    token = register_and_get_token(client, "createtaskuser")
    headers = {"Authorization": f"Bearer {token}"}
    project_id = create_project_for_user(client, token, "CreateTaskProject")

    task_payload = {**TASK_CREATE_DATA_1, "project_id": project_id}
    response = client.post("/api/tasks/", json=task_payload, headers=headers)
    assert response.status_code == 201 # As per api.md
    data = response.json()
    assert data["title"] == TASK_CREATE_DATA_1["title"]
    assert data["project_id"] == project_id
    assert "id" in data
    assert data["completed"] is False # Default
    assert data["priority"] == 0 # Default

    # Test creating task with missing required fields (e.g., title, project_id)
    response_missing_title = client.post("/api/tasks/", json={"project_id": project_id, "description": "Task no title"}, headers=headers)
    assert response_missing_title.status_code == 422

    response_missing_project = client.post("/api/tasks/", json={"title": "No Project Task"}, headers=headers)
    assert response_missing_project.status_code == 422


def test_get_tasks_with_filters(client: TestClient):
    token = register_and_get_token(client, "gettasksuser")
    headers = {"Authorization": f"Bearer {token}"}
    project1_id = create_project_for_user(client, token, "P1")
    project2_id = create_project_for_user(client, token, "P2")

    # Create some tasks
    task1_p1 = client.post("/api/tasks/", json={"title": "T1P1 Active Low", "project_id": project1_id, "priority": 0, "completed": False, "due_date": "2024-01-10T10:00:00Z"}, headers=headers).json()
    task2_p1 = client.post("/api/tasks/", json={"title": "T2P1 Completed High", "project_id": project1_id, "priority": 2, "completed": True, "due_date": "2024-01-05T10:00:00Z"}, headers=headers).json()
    task1_p2 = client.post("/api/tasks/", json={"title": "T1P2 Active Medium", "project_id": project2_id, "priority": 1, "completed": False}, headers=headers).json()

    # Get all tasks for the user (should be 3)
    response_all = client.get("/api/tasks/", headers=headers)
    assert response_all.status_code == 200
    # The default for 'archived' projects is False, so tasks from archived projects might not show.
    # Assuming projects created by helper are not archived by default.
    # The 'get_tasks' router does not filter by project's archived status, only task properties.
    assert len(response_all.json()) == 3

    # Filter by project_id
    response_proj1 = client.get(f"/api/tasks/?project_id={project1_id}", headers=headers)
    assert response_proj1.status_code == 200
    assert len(response_proj1.json()) == 2

    # Filter by completed status
    response_completed = client.get("/api/tasks/?completed=true", headers=headers)
    assert response_completed.status_code == 200
    assert len(response_completed.json()) == 1
    assert response_completed.json()[0]["title"] == "T2P1 Completed High"

    response_active = client.get("/api/tasks/?completed=false", headers=headers)
    assert response_active.status_code == 200
    assert len(response_active.json()) == 2

    # Filter by priority
    response_priority2 = client.get("/api/tasks/?priority=2", headers=headers)
    assert response_priority2.status_code == 200
    assert len(response_priority2.json()) == 1
    assert response_priority2.json()[0]["title"] == "T2P1 Completed High"

    # Filter by due_date (using tasks from project1)
    response_due_before = client.get(f"/api/tasks/?project_id={project1_id}&due_date_end=2024-01-07T00:00:00Z", headers=headers)
    assert response_due_before.status_code == 200
    assert len(response_due_before.json()) == 1
    assert response_due_before.json()[0]["title"] == "T2P1 Completed High"

    response_due_after = client.get(f"/api/tasks/?project_id={project1_id}&due_date_start=2024-01-07T00:00:00Z", headers=headers)
    assert response_due_after.status_code == 200
    assert len(response_due_after.json()) == 1
    assert response_due_after.json()[0]["title"] == "T1P1 Active Low"

    # Test pagination (limit, skip) - ensure enough tasks exist for this
    client.post("/api/tasks/", json={"title": "T2P2 Pagination Test", "project_id": project2_id}, headers=headers) # Now 4 tasks total for user
    response_limit2 = client.get("/api/tasks/?limit=2", headers=headers)
    assert response_limit2.status_code == 200
    assert len(response_limit2.json()) == 2

    response_skip1_limit2 = client.get("/api/tasks/?skip=1&limit=2", headers=headers)
    assert response_skip1_limit2.status_code == 200
    assert len(response_skip1_limit2.json()) == 2


def test_get_task_by_id(client: TestClient):
    token = register_and_get_token(client, "gettaskbyiduser")
    headers = {"Authorization": f"Bearer {token}"}
    project_id = create_project_for_user(client, token, "GetTaskByIDProject")

    task_payload = {**TASK_CREATE_DATA_1, "project_id": project_id}
    create_response = client.post("/api/tasks/", json=task_payload, headers=headers)
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    response = client.get(f"/api/tasks/{task_id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == task_id
    assert data["title"] == TASK_CREATE_DATA_1["title"]

    # Test getting non-existent task
    response_not_found = client.get(f"/api/tasks/999999", headers=headers)
    assert response_not_found.status_code == 404

    # Test getting task not owned by user (via project ownership)
    token_other_user = register_and_get_token(client, "othergettaskuser")
    headers_other_user = {"Authorization": f"Bearer {token_other_user}"}
    response_forbidden = client.get(f"/api/tasks/{task_id}", headers=headers_other_user)
    assert response_forbidden.status_code == 404

def test_update_task(client: TestClient):
    token = register_and_get_token(client, "updatetaskuser")
    headers = {"Authorization": f"Bearer {token}"}
    project_id = create_project_for_user(client, token, "UpdateTaskProject")

    task_payload = {**TASK_CREATE_DATA_1, "project_id": project_id}
    create_response = client.post("/api/tasks/", json=task_payload, headers=headers)
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    update_payload = {
        "title": "Updated API Task Title",
        "description": "This task has been updated via API.",
        "completed": True,
        "priority": 1,
        "due_date": "2025-01-01T12:00:00Z"
    }
    response = client.put(f"/api/tasks/{task_id}", json=update_payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == task_id
    assert data["title"] == update_payload["title"]
    assert data["description"] == update_payload["description"]
    assert data["completed"] is True
    assert data["priority"] == 1
    assert data["due_date"] == "2025-01-01T12:00:00" # Response does not include 'Z'

    # Test updating task not owned by user
    token_other_user = register_and_get_token(client, "otherupdatetaskuser")
    headers_other_user = {"Authorization": f"Bearer {token_other_user}"}
    response_forbidden = client.put(f"/api/tasks/{task_id}", json=update_payload, headers=headers_other_user)
    assert response_forbidden.status_code == 404

def test_delete_task(client: TestClient):
    token = register_and_get_token(client, "deletetaskuser")
    headers = {"Authorization": f"Bearer {token}"}
    project_id = create_project_for_user(client, token, "DeleteTaskProject")

    task_payload = {**TASK_CREATE_DATA_1, "project_id": project_id}
    create_response = client.post("/api/tasks/", json=task_payload, headers=headers)
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    response = client.delete(f"/api/tasks/{task_id}", headers=headers)
    assert response.status_code == 204

    # Verify task is deleted
    get_response = client.get(f"/api/tasks/{task_id}", headers=headers)
    assert get_response.status_code == 404

    # Test deleting non-existent task
    response_not_found = client.delete(f"/api/tasks/999999", headers=headers)
    assert response_not_found.status_code == 404

# --- Tag related Task API Tests ---

def test_manage_task_tags(client: TestClient):
    token = register_and_get_token(client, "tasktagsuser")
    headers = {"Authorization": f"Bearer {token}"}
    project_id = create_project_for_user(client, token, "TaskTagProject")

    task_payload = {**TASK_CREATE_DATA_1, "project_id": project_id}
    task_create_response = client.post("/api/tasks/", json=task_payload, headers=headers)
    assert task_create_response.status_code == 201
    task_id = task_create_response.json()["id"]

    tag1_id = create_tag_for_user(client, token, "Tag1")
    tag2_id = create_tag_for_user(client, token, "Tag2")

    # Add tag1 to task
    response_add_tag1 = client.post(f"/api/tasks/{task_id}/tags/{tag1_id}", headers=headers)
    # Assuming 200 OK if Task schema is returned, or 201 if only status.
    # Router /api/tasks/{task_id}/tags/{tag_id} (POST) has status_code=status.HTTP_201_CREATED
    assert response_add_tag1.status_code == 201
    task_data_after_add1 = response_add_tag1.json()
    assert any(tag["id"] == tag1_id for tag in task_data_after_add1["tags"])

    # Add tag2 to task
    response_add_tag2 = client.post(f"/api/tasks/{task_id}/tags/{tag2_id}", headers=headers)
    assert response_add_tag2.status_code == 201
    task_data_after_add2 = response_add_tag2.json()
    assert len(task_data_after_add2["tags"]) == 2
    assert any(tag["id"] == tag2_id for tag in task_data_after_add2["tags"])

    # Get tags for task
    response_get_tags = client.get(f"/api/tasks/{task_id}/tags", headers=headers) # Removed trailing slash
    assert response_get_tags.status_code == 200
    tags_on_task = response_get_tags.json()
    assert len(tags_on_task) == 2
    assert any(tag["id"] == tag1_id for tag in tags_on_task)
    assert any(tag["id"] == tag2_id for tag in tags_on_task)

    # Remove tag1 from task
    response_remove_tag1 = client.delete(f"/api/tasks/{task_id}/tags/{tag1_id}", headers=headers)
    # Router /api/tasks/{task_id}/tags/{tag_id} (DELETE) has status_code=status.HTTP_204_NO_CONTENT
    assert response_remove_tag1.status_code == 204

    # Verify tag removed by getting the task again
    task_after_remove_response = client.get(f"/api/tasks/{task_id}", headers=headers)
    assert task_after_remove_response.status_code == 200
    task_data_after_remove1 = task_after_remove_response.json()
    assert len(task_data_after_remove1["tags"]) == 1
    assert not any(tag["id"] == tag1_id for tag in task_data_after_remove1["tags"])
    assert any(tag["id"] == tag2_id for tag in task_data_after_remove1["tags"])

    # Test adding tag not owned by user (should fail, or tag not found for user)
    token_other_user = register_and_get_token(client, "othertagowner")
    other_user_tag_id = create_tag_for_user(client, token_other_user, "OtherUserTag")
    response_add_other_tag = client.post(f"/api/tasks/{task_id}/tags/{other_user_tag_id}", headers=headers)
    # This should fail because the current user (token) does not own other_user_tag_id
    # crud.add_tag_to_task checks ownership of both task and tag against user_id
    assert response_add_other_tag.status_code == 404 # Tag not found for this user

# TODO: Add tests for subtasks (POST /api/tasks/{task_id}/subtasks) if parent_task_id is implemented
# TODO: Add tests for task reordering (PUT /api/tasks/reorder)
