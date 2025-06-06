import pytest
from sqlalchemy.orm import Session
from app import crud, schemas, models # Assuming models are needed for asserts
import datetime

# Helper function to create a dummy user for testing project ownership
def create_test_user(db_session: Session, email="owner@example.com", username="projectowner") -> models.User:
    user_in = schemas.UserCreate(email=email, username=username, password="ownerpassword")
    return crud.create_user(db_session, user_create=user_in)

# --- Test Data ---
PROJECT_TEST_DATA_1 = {
    "name": "Test Project 1",
    "description": "Description for test project 1",
}

PROJECT_TEST_DATA_2 = {
    "name": "Test Project 2",
    "description": "Description for test project 2",
    "is_archived": True, # Test with archived status
    # archived_at will be set by the CRUD operation if is_archived is True
}

# --- Tests for Project CRUD operations ---

def test_create_project(db_session: Session):
    owner = create_test_user(db_session)
    project_in = schemas.ProjectCreate(**PROJECT_TEST_DATA_1)
    db_project = crud.create_project(db_session, project_create=project_in, owner_id=owner.id)

    assert db_project is not None
    assert db_project.name == PROJECT_TEST_DATA_1["name"]
    assert db_project.description == PROJECT_TEST_DATA_1["description"]
    assert db_project.owner_id == owner.id
    assert db_project.id is not None
    assert db_project.is_archived is False # Default
    assert db_project.archived_at is None # Default

    # Test creating an archived project
    # crud.create_project should handle setting archived_at if is_archived is true in ProjectCreate
    project_archived_in = schemas.ProjectCreate(**PROJECT_TEST_DATA_2)
    db_project_archived = crud.create_project(db_session, project_create=project_archived_in, owner_id=owner.id)
    assert db_project_archived.is_archived is True
    # If is_archived is True on creation, archived_at should be set.
    # This depends on the implementation of crud.create_project.
    # If crud.create_project only sets is_archived and relies on update for archived_at, this test might need adjustment
    # or the crud function needs to ensure archived_at is set.
    # For now, assuming crud.create_project handles this.
    assert db_project_archived.archived_at is not None


def test_get_project(db_session: Session):
    owner = create_test_user(db_session)
    project_in = schemas.ProjectCreate(**PROJECT_TEST_DATA_1)
    created_project = crud.create_project(db_session, project_create=project_in, owner_id=owner.id)

    # Test get by owner
    retrieved_project_owner = crud.get_project(db_session, project_id=created_project.id, user_id=owner.id)
    assert retrieved_project_owner is not None
    assert retrieved_project_owner.id == created_project.id
    assert retrieved_project_owner.name == created_project.name

    # Test get without owner check (should still work if project exists and crud.get_project allows it)
    # Assuming crud.get_project(db, project_id) without user_id is for system access or specific use cases.
    # If user_id is mandatory for get_project, this part of the test would be invalid.
    # The prompt's test implies get_project can be called without user_id.
    retrieved_project_no_owner_check = crud.get_project(db_session, project_id=created_project.id)
    assert retrieved_project_no_owner_check is not None
    assert retrieved_project_no_owner_check.id == created_project.id

    # Test get for a different user (should be None if user_id is used for authorization)
    other_owner = create_test_user(db_session, email="other@example.com", username="otherowner")
    retrieved_project_other_owner = crud.get_project(db_session, project_id=created_project.id, user_id=other_owner.id)
    assert retrieved_project_other_owner is None

    non_existent_project = crud.get_project(db_session, project_id=99999, user_id=owner.id)
    assert non_existent_project is None

def test_get_projects_by_user(db_session: Session):
    owner1 = create_test_user(db_session, email="owner1@example.com", username="owner1")
    owner2 = create_test_user(db_session, email="owner2@example.com", username="owner2")

    crud.create_project(db_session, project_create=schemas.ProjectCreate(name="P1O1", description="."), owner_id=owner1.id)
    crud.create_project(db_session, project_create=schemas.ProjectCreate(name="P2O1", description=".", is_archived=True), owner_id=owner1.id)
    crud.create_project(db_session, project_create=schemas.ProjectCreate(name="P1O2", description="."), owner_id=owner2.id)

    # Get all projects for owner1
    projects_owner1 = crud.get_projects_by_user(db_session, user_id=owner1.id)
    assert len(projects_owner1) == 2

    # Get non-archived projects for owner1
    projects_owner1_non_archived = crud.get_projects_by_user(db_session, user_id=owner1.id, archived=False)
    assert len(projects_owner1_non_archived) == 1
    assert projects_owner1_non_archived[0].name == "P1O1"

    # Get archived projects for owner1
    projects_owner1_archived = crud.get_projects_by_user(db_session, user_id=owner1.id, archived=True)
    assert len(projects_owner1_archived) == 1
    assert projects_owner1_archived[0].name == "P2O1"

    # Test pagination
    projects_owner1_limit1 = crud.get_projects_by_user(db_session, user_id=owner1.id, limit=1)
    assert len(projects_owner1_limit1) == 1

    projects_owner1_skip1 = crud.get_projects_by_user(db_session, user_id=owner1.id, skip=1, limit=1) # Added limit for predictable result
    assert len(projects_owner1_skip1) == 1
    # The order is not guaranteed unless crud.get_projects_by_user has an order_by clause.
    # For now, we just check the count. If specific order is needed, crud needs to support it.


def test_update_project(db_session: Session):
    owner = create_test_user(db_session)
    project_in = schemas.ProjectCreate(**PROJECT_TEST_DATA_1)
    db_project = crud.create_project(db_session, project_create=project_in, owner_id=owner.id)

    update_data = schemas.ProjectUpdate(
        name="Updated Project Name",
        description="Updated description.",
        is_archived=True
    )

    # Store current time before update for comparison
    time_before_update = datetime.datetime.utcnow() - datetime.timedelta(seconds=1) # Ensure it's slightly in the past

    updated_project = crud.update_project(db_session, db_project=db_project, project_update=update_data)

    assert updated_project is not None
    assert updated_project.id == db_project.id
    assert updated_project.name == "Updated Project Name"
    assert updated_project.description == "Updated description."
    assert updated_project.is_archived is True
    assert updated_project.archived_at is not None
    assert updated_project.archived_at > time_before_update

    # Test unarchiving
    unarchive_data = schemas.ProjectUpdate(is_archived=False)
    # time_before_unarchive = datetime.datetime.utcnow() - datetime.timedelta(seconds=1) # Not strictly needed for this check
    unarchived_project = crud.update_project(db_session, db_project=updated_project, project_update=unarchive_data)
    assert unarchived_project.is_archived is False
    assert unarchived_project.archived_at is None # Assuming crud.update_project nullifies archived_at when unarchiving

    # Test partial update
    partial_update_data = schemas.ProjectUpdate(name="Partially Updated Name")
    partially_updated_project = crud.update_project(db_session, db_project=unarchived_project, project_update=partial_update_data)
    assert partially_updated_project.name == "Partially Updated Name"
    assert partially_updated_project.description == "Updated description." # Should remain from previous update


def test_delete_project(db_session: Session):
    owner = create_test_user(db_session)
    project_in = schemas.ProjectCreate(**PROJECT_TEST_DATA_1)
    created_project = crud.create_project(db_session, project_create=project_in, owner_id=owner.id)

    # Test deletion by owner
    deleted_project = crud.delete_project(db_session, project_id=created_project.id, user_id=owner.id)
    assert deleted_project is not None
    assert deleted_project.id == created_project.id

    retrieved_after_delete = crud.get_project(db_session, project_id=created_project.id, user_id=owner.id)
    assert retrieved_after_delete is None

    # Test deleting non-existent project
    non_existent_deleted_project = crud.delete_project(db_session, project_id=99999, user_id=owner.id)
    assert non_existent_deleted_project is None

    # Test attempting to delete project owned by another user
    project_to_keep = crud.create_project(db_session, project_create=schemas.ProjectCreate(name="P_Kept", description="."), owner_id=owner.id)
    other_owner = create_test_user(db_session, email="other2@example.com", username="otherowner2")
    failed_delete_attempt = crud.delete_project(db_session, project_id=project_to_keep.id, user_id=other_owner.id)
    assert failed_delete_attempt is None # Expecting None if user_id check fails in crud.delete_project
    assert crud.get_project(db_session, project_id=project_to_keep.id, user_id=owner.id) is not None # Ensure it's still there
