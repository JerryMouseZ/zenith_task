import pytest
from sqlalchemy.orm import Session
from app import crud, schemas, models
import datetime
import time # For more unique names

# Helper function to create a dummy user
def create_test_user(db_session: Session, email_suffix="user@example.com", username_suffix="taskuser") -> models.User:
    # Ensure unique email and username for each call
    # Using a combination of suffix and timestamp for higher chance of uniqueness
    unique_part = f"{time.time_ns()}" # nanoseconds for higher granularity
    email = f"{username_suffix}_{unique_part}@example.com"
    username = f"{username_suffix}_{unique_part}"
    user_in = schemas.UserCreate(email=email, username=username, password="taskpassword")
    return crud.create_user(db_session, user_create=user_in)

# Helper function to create a dummy project
def create_test_project(db_session: Session, owner_id: int, name_suffix="Project") -> models.Project:
    unique_part = f"{time.time_ns()}"
    project_in = schemas.ProjectCreate(name=f"Task Test {name_suffix} {unique_part}", description="Test project for tasks")
    return crud.create_project(db_session, project_create=project_in, owner_id=owner_id)

# Helper function to create a dummy tag
def create_test_tag(db_session: Session, user_id: int, name_suffix="Tag") -> models.Tag:
    unique_part = f"{time.time_ns()}"
    tag_name = f"Test {name_suffix} {unique_part}"
    tag_in = schemas.TagCreate(name=tag_name, color="#FF0000")

    # Check if tag already exists by this name for this user first
    existing_tag = crud.get_tag_by_name(db_session, name=tag_name, user_id=user_id)
    if existing_tag:
        return existing_tag
    return crud.create_tag(db_session, tag_create=tag_in, user_id=user_id)


# --- Test Data ---
TASK_TEST_DATA_1 = {
    "title": "Test Task 1",
    "description": "Description for task 1",
}

TASK_TEST_DATA_2 = {
    "title": "Test Task 2",
    "description": "Description for task 2",
    "completed": True,
    "priority": 1,
}

# --- Tests for Task CRUD operations ---

def test_create_task(db_session: Session):
    owner = create_test_user(db_session, username_suffix="createtaskowner")
    project = create_test_project(db_session, owner_id=owner.id)

    task_in_data = {**TASK_TEST_DATA_1, "project_id": project.id}
    task_in = schemas.TaskCreate(**task_in_data)
    db_task = crud.create_task(db_session, task_create=task_in)

    assert db_task is not None
    assert db_task.title == TASK_TEST_DATA_1["title"]
    assert db_task.description == TASK_TEST_DATA_1["description"]
    assert db_task.project_id == project.id
    # Ownership is via project: db_task.project.owner_id == owner.id
    # This is implicitly tested by other tests like get_task with user_id
    assert db_task.id is not None
    assert db_task.completed is False # Default
    assert db_task.priority == 0 # Default
    assert db_task.assignee_id is None # Default

    # Test creating a task with an assignee
    assignee = create_test_user(db_session, username_suffix="taskassignee")
    task_with_assignee_data = {**TASK_TEST_DATA_2, "project_id": project.id, "assignee_id": assignee.id}
    task_with_assignee_in = schemas.TaskCreate(**task_with_assignee_data)
    db_task_assigned = crud.create_task(db_session, task_create=task_with_assignee_in)
    assert db_task_assigned.assignee_id == assignee.id
    assert db_task_assigned.completed is True
    assert db_task_assigned.priority == 1

def test_get_task(db_session: Session):
    owner = create_test_user(db_session, username_suffix="gettaskowner")
    project = create_test_project(db_session, owner_id=owner.id)
    task_in_data = {**TASK_TEST_DATA_1, "project_id": project.id}
    task_in = schemas.TaskCreate(**task_in_data)
    created_task = crud.create_task(db_session, task_create=task_in)

    # Test get by owner of project
    retrieved_task = crud.get_task(db_session, task_id=created_task.id, user_id=owner.id)
    assert retrieved_task is not None
    assert retrieved_task.id == created_task.id
    assert retrieved_task.title == created_task.title

    # Test get without user_id (should still work if task exists and CRUD allows it)
    retrieved_task_no_user = crud.get_task(db_session, task_id=created_task.id) # Assuming user_id is optional in get_task
    assert retrieved_task_no_user is not None

    # Test get for a different user (should be None)
    other_user = create_test_user(db_session, username_suffix="othertaskuser")
    retrieved_task_other_user = crud.get_task(db_session, task_id=created_task.id, user_id=other_user.id)
    assert retrieved_task_other_user is None

    non_existent_task = crud.get_task(db_session, task_id=99999, user_id=owner.id)
    assert non_existent_task is None

def test_get_tasks(db_session: Session):
    owner = create_test_user(db_session, username_suffix="gettasksowner")
    project1 = create_test_project(db_session, owner_id=owner.id, name_suffix="P1")
    project2 = create_test_project(db_session, owner_id=owner.id, name_suffix="P2")

    # Tasks for project1
    crud.create_task(db_session, schemas.TaskCreate(title="T1P1", project_id=project1.id, completed=False, priority=0, due_date=datetime.datetime(2024, 1, 10)))
    crud.create_task(db_session, schemas.TaskCreate(title="T2P1", project_id=project1.id, completed=True, priority=1, due_date=datetime.datetime(2024, 1, 5)))

    # Task for project2
    crud.create_task(db_session, schemas.TaskCreate(title="T1P2", project_id=project2.id, completed=False, priority=0))

    # Another user's task - should not appear
    other_owner = create_test_user(db_session, username_suffix="othertasksowner")
    other_project = create_test_project(db_session, owner_id=other_owner.id, name_suffix="OtherP")
    crud.create_task(db_session, schemas.TaskCreate(title="OtherUserTask", project_id=other_project.id))

    # Get all tasks for owner
    all_owner_tasks = crud.get_tasks(db_session, user_id=owner.id)
    assert len(all_owner_tasks) == 3

    # Filter by project_id
    p1_tasks = crud.get_tasks(db_session, user_id=owner.id, project_id=project1.id)
    assert len(p1_tasks) == 2
    assert all(t.project_id == project1.id for t in p1_tasks)

    # Filter by completed status
    completed_tasks = crud.get_tasks(db_session, user_id=owner.id, completed=True)
    assert len(completed_tasks) == 1
    assert completed_tasks[0].title == "T2P1"

    # Filter by priority
    priority_1_tasks = crud.get_tasks(db_session, user_id=owner.id, priority=1)
    assert len(priority_1_tasks) == 1
    assert priority_1_tasks[0].title == "T2P1"

    # Filter by due_date_before
    due_before_tasks = crud.get_tasks(db_session, user_id=owner.id, project_id=project1.id, due_date_before=datetime.datetime(2024, 1, 7))
    assert len(due_before_tasks) == 1
    assert due_before_tasks[0].title == "T2P1"

    # Filter by due_date_after
    due_after_tasks = crud.get_tasks(db_session, user_id=owner.id, project_id=project1.id, due_date_after=datetime.datetime(2024, 1, 7))
    assert len(due_after_tasks) == 1
    assert due_after_tasks[0].title == "T1P1"

    # Test pagination
    paginated_tasks = crud.get_tasks(db_session, user_id=owner.id, limit=1, skip=0)
    assert len(paginated_tasks) == 1

def test_update_task(db_session: Session):
    owner = create_test_user(db_session, username_suffix="updatetaskowner")
    project = create_test_project(db_session, owner_id=owner.id)
    task_in_data = {**TASK_TEST_DATA_1, "project_id": project.id}
    task_in = schemas.TaskCreate(**task_in_data)
    db_task = crud.create_task(db_session, task_create=task_in)

    update_data = schemas.TaskUpdate(
        title="Updated Task Title",
        description="Updated task description.",
        completed=True,
        priority=2,
        due_date=datetime.datetime(2025, 1, 1)
    )
    # crud.update_task does not take user_id; ownership should be checked before calling,
    # e.g., by ensuring db_task was fetched with user_id scope.
    updated_task = crud.update_task(db_session, db_task=db_task, task_update=update_data)

    assert updated_task is not None
    assert updated_task.id == db_task.id
    assert updated_task.title == "Updated Task Title"
    assert updated_task.description == "Updated task description."
    assert updated_task.completed is True
    assert updated_task.priority == 2
    assert updated_task.due_date == datetime.datetime(2025, 1, 1)

    # Test partial update (only title)
    partial_update = schemas.TaskUpdate(title="Partially Updated Title")
    partially_updated_task = crud.update_task(db_session, db_task=updated_task, task_update=partial_update)
    assert partially_updated_task.title == "Partially Updated Title"
    assert partially_updated_task.completed is True # Should remain from previous update

    # Test update by non-owner (should fail if router logic prevents it)
    # The crud.update_task itself doesn't check user_id, relies on router to pass correct db_task.
    # To test this properly, one would try to fetch db_task as other_user, which would fail.
    # Then, if it somehow proceeded, the update would apply to the object.
    # The test for non-owner update is better at the API level or by ensuring router correctly denies access.
    # For this CRUD test, we assume db_task is the correct one.
    # The current test structure for non-owner update here is trying to pass other_user.id to a function that doesn't take it.
    # Let's simulate the check that router would do:
    other_user = create_test_user(db_session, username_suffix="otherupdatetask")
    task_as_other_user = crud.get_task(db_session, task_id=db_task.id, user_id=other_user.id)
    assert task_as_other_user is None # This other_user should not get the task

    # If task_as_other_user was passed to update_task (hypothetically, if it was not None), then it would update.
    # But since it's None, the update attempt wouldn't happen via a correctly implemented router.
    # The original test logic:
    # fail_update_data = schemas.TaskUpdate(title="Should Not Update")
    # failed_update_task = crud.update_task(db_session, db_task=db_task, task_update=fail_update_data, user_id=other_user.id)
    # assert failed_update_task is None
    # This failed because user_id is not an arg. The spirit of the test is that other_user can't update owner's task.
    # This is ensured by the router using get_task with other_user.id, finding nothing, and thus not calling update_task.
    db_session.refresh(db_task) # Refresh state from DB
    assert db_task.title == "Partially Updated Title" # Should not have changed to "Should Not Update"


def test_delete_task(db_session: Session):
    owner = create_test_user(db_session, username_suffix="deletetaskowner")
    project = create_test_project(db_session, owner_id=owner.id)
    task_in_data = {**TASK_TEST_DATA_1, "project_id": project.id}
    task_in = schemas.TaskCreate(**task_in_data)
    created_task = crud.create_task(db_session, task_create=task_in)

    # Test deletion by owner
    deleted_task = crud.delete_task(db_session, task_id=created_task.id, user_id=owner.id)
    assert deleted_task is not None
    assert deleted_task.id == created_task.id

    retrieved_after_delete = crud.get_task(db_session, task_id=created_task.id, user_id=owner.id)
    assert retrieved_after_delete is None

    # Test deleting non-existent task
    non_existent_deleted_task = crud.delete_task(db_session, task_id=99999, user_id=owner.id)
    assert non_existent_deleted_task is None

    # Test attempting to delete task owned by another user's project
    task_to_keep_in = schemas.TaskCreate(title="Keep", project_id=project.id)
    task_to_keep = crud.create_task(db_session, task_create=task_to_keep_in)
    other_user = create_test_user(db_session, username_suffix="otherdeletetask")
    failed_delete_attempt = crud.delete_task(db_session, task_id=task_to_keep.id, user_id=other_user.id)
    assert failed_delete_attempt is None
    assert crud.get_task(db_session, task_id=task_to_keep.id, user_id=owner.id) is not None


def test_add_remove_tag_to_task(db_session: Session):
    owner = create_test_user(db_session, username_suffix="tagtaskowner")
    project = create_test_project(db_session, owner_id=owner.id)
    task_in_data = {**TASK_TEST_DATA_1, "project_id": project.id}
    task_in = schemas.TaskCreate(**task_in_data)
    db_task = crud.create_task(db_session, task_create=task_in)

    tag1 = create_test_tag(db_session, user_id=owner.id, name_suffix="T1")
    tag2 = create_test_tag(db_session, user_id=owner.id, name_suffix="T2")

    # Add tag1
    task_with_tag1 = crud.add_tag_to_task(db_session, task_id=db_task.id, tag_id=tag1.id, user_id=owner.id)
    assert task_with_tag1 is not None
    assert len(task_with_tag1.tags) == 1
    assert tag1 in task_with_tag1.tags

    # Add tag2
    task_with_tags = crud.add_tag_to_task(db_session, task_id=db_task.id, tag_id=tag2.id, user_id=owner.id)
    assert len(task_with_tags.tags) == 2
    assert tag2 in task_with_tags.tags

    # Try adding same tag again (should not duplicate)
    task_same_tag = crud.add_tag_to_task(db_session, task_id=db_task.id, tag_id=tag1.id, user_id=owner.id)
    assert len(task_same_tag.tags) == 2

    # Remove tag1
    task_after_remove = crud.remove_tag_from_task(db_session, task_id=db_task.id, tag_id=tag1.id, user_id=owner.id)
    assert task_after_remove is not None
    assert len(task_after_remove.tags) == 1
    assert tag1 not in task_after_remove.tags
    assert tag2 in task_after_remove.tags

    # Try removing non-associated tag
    task_remove_non_tag = crud.remove_tag_from_task(db_session, task_id=db_task.id, tag_id=tag1.id, user_id=owner.id) # tag1 is already removed
    assert len(task_remove_non_tag.tags) == 1

    # Test permissions: other user cannot add tag to a task they don't own
    other_user = create_test_user(db_session, username_suffix="othertaguser")
    other_user_tag = create_test_tag(db_session, user_id=other_user.id, name_suffix="OtherUserTag") # Tag owned by other_user
    failed_add_other_user = crud.add_tag_to_task(db_session, task_id=db_task.id, tag_id=other_user_tag.id, user_id=other_user.id)
    assert failed_add_other_user is None

    # Test permissions: owner cannot add other user's tag to their own task
    # This depends on crud.add_tag_to_task checking that the tag being added also belongs to the user_id passed.
    # crud.add_tag_to_task should fetch the tag ensuring it belongs to user_id.
    failed_add_foreign_tag = crud.add_tag_to_task(db_session, task_id=db_task.id, tag_id=other_user_tag.id, user_id=owner.id)
    assert failed_add_foreign_tag is None


def test_get_tags_for_task(db_session: Session):
    owner = create_test_user(db_session, username_suffix="gettagstaskowner")
    project = create_test_project(db_session, owner_id=owner.id)
    task_in_data = {**TASK_TEST_DATA_1, "project_id": project.id}
    task_in = schemas.TaskCreate(**task_in_data)
    db_task = crud.create_task(db_session, task_create=task_in)

    tag1 = create_test_tag(db_session, user_id=owner.id, name_suffix="GetT1")
    tag2 = create_test_tag(db_session, user_id=owner.id, name_suffix="GetT2")

    crud.add_tag_to_task(db_session, task_id=db_task.id, tag_id=tag1.id, user_id=owner.id)
    crud.add_tag_to_task(db_session, task_id=db_task.id, tag_id=tag2.id, user_id=owner.id)

    tags_on_task = crud.get_tags_for_task(db_session, task_id=db_task.id, user_id=owner.id)
    assert tags_on_task is not None # Should return a list, even if empty
    assert len(tags_on_task) == 2
    tag_names_on_task = {tag.name for tag in tags_on_task}
    assert tag1.name in tag_names_on_task
    assert tag2.name in tag_names_on_task

    # Test for task with no tags
    task_no_tags_data = {**TASK_TEST_DATA_2, "project_id": project.id} # Using different data
    task_no_tags_in = schemas.TaskCreate(**task_no_tags_data)
    db_task_no_tags = crud.create_task(db_session, task_create=task_no_tags_in)
    tags_on_empty_task = crud.get_tags_for_task(db_session, task_id=db_task_no_tags.id, user_id=owner.id)
    assert tags_on_empty_task is not None
    assert len(tags_on_empty_task) == 0

    # Test permission: other user cannot get tags for task they don't own
    other_user = create_test_user(db_session, username_suffix="othergettagstask")
    failed_get = crud.get_tags_for_task(db_session, task_id=db_task.id, user_id=other_user.id)
    assert failed_get is not None # crud.get_tags_for_task likely returns [] if task not found for user
    assert len(failed_get) == 0
