import pytest
from sqlalchemy.orm import Session
from app import crud, schemas, models
import datetime
import time

# Helper function to create a dummy user
def create_test_user(db_session: Session, username_suffix="focustestuser") -> models.User:
    email = f"{username_suffix}{time.time_ns()}@example.com"
    username = f"{username_suffix}{time.time_ns()}"
    user_in = schemas.UserCreate(email=email, username=username, password="fspassword")
    return crud.create_user(db_session, user_create=user_in)

# Helper function to create a dummy project
def create_test_project(db_session: Session, owner_id: int) -> models.Project:
    project_in = schemas.ProjectCreate(name=f"Focus Test Project {time.time_ns()}", description="Test project for focus sessions")
    return crud.create_project(db_session, project_create=project_in, owner_id=owner_id)

# Helper function to create a dummy task
def create_test_task(db_session: Session, project_id: int, owner_id: int) -> models.Task:
    # Ensure owner_id for the task is consistent with project owner for permission checks if any in crud.create_task
    # The TaskCreate schema now includes 'completed' field.
    task_in = schemas.TaskCreate(title=f"Focus Test Task {time.time_ns()}", project_id=project_id, completed=False)
    return crud.create_task(db_session, task_create=task_in)


# --- Test Data ---
NOW = datetime.datetime.utcnow()
LATER = NOW + datetime.timedelta(hours=1)

FOCUS_SESSION_DATA_1 = {
    "start_time": NOW,
    "end_time": LATER,
    "status": schemas.FocusSessionStatus.COMPLETED,
    "notes": "Good focus session."
}

FOCUS_SESSION_DATA_2 = {
    "start_time": NOW - datetime.timedelta(days=1),
    "end_time": NOW - datetime.timedelta(days=1, hours=-1), # Ended 1 hour later yesterday
    "status": schemas.FocusSessionStatus.ACTIVE, # Changed to ACTIVE for variety
    "notes": "Ongoing session."
}


# --- Tests for FocusSession CRUD operations ---

def test_create_focus_session(db_session: Session):
    user = create_test_user(db_session)
    project = create_test_project(db_session, owner_id=user.id)
    task = create_test_task(db_session, project_id=project.id, owner_id=user.id)

    session_in_data = {**FOCUS_SESSION_DATA_1, "task_id": task.id}
    session_in = schemas.FocusSessionCreate(**session_in_data)

    db_session_obj = crud.create_focus_session(db_session, session_create=session_in, user_id=user.id)

    assert db_session_obj is not None
    assert db_session_obj.user_id == user.id
    assert db_session_obj.task_id == task.id
    assert db_session_obj.start_time == FOCUS_SESSION_DATA_1["start_time"]
    assert db_session_obj.end_time == FOCUS_SESSION_DATA_1["end_time"]
    assert db_session_obj.status.value == schemas.FocusSessionStatus.COMPLETED.value
    assert db_session_obj.notes == FOCUS_SESSION_DATA_1["notes"]
    assert db_session_obj.id is not None

    # Test creating a session without a task_id
    # session_no_task_data = {key: val for key, val in FOCUS_SESSION_DATA_1.items() if key != "task_id"}
    # Need to ensure required fields like start_time are present
    session_no_task_in = schemas.FocusSessionCreate(
        start_time=FOCUS_SESSION_DATA_1["start_time"],
        end_time=FOCUS_SESSION_DATA_1["end_time"], # end_time is optional in base, but provided here
        status=FOCUS_SESSION_DATA_1["status"], # status has a default in base
        notes=FOCUS_SESSION_DATA_1["notes"] # notes is optional
        # task_id is optional in FocusSessionBase and thus FocusSessionCreate
    )
    db_session_no_task = crud.create_focus_session(db_session, session_create=session_no_task_in, user_id=user.id)
    assert db_session_no_task is not None
    assert db_session_no_task.user_id == user.id
    assert db_session_no_task.task_id is None


def test_get_focus_session(db_session: Session):
    user = create_test_user(db_session)
    # Create a session without a task_id, as task_id is Optional in FocusSessionCreate
    session_create_schema = schemas.FocusSessionCreate(
        start_time=FOCUS_SESSION_DATA_1["start_time"],
        end_time=FOCUS_SESSION_DATA_1["end_time"],
        status=FOCUS_SESSION_DATA_1["status"],
        notes=FOCUS_SESSION_DATA_1["notes"]
    )
    created_session = crud.create_focus_session(db_session, session_create=session_create_schema, user_id=user.id)

    retrieved_session = crud.get_focus_session(db_session, session_id=created_session.id, user_id=user.id)
    assert retrieved_session is not None
    assert retrieved_session.id == created_session.id
    assert retrieved_session.user_id == user.id

    # Test get for a different user (should be None)
    other_user = create_test_user(db_session, username_suffix="otherfsuser")
    retrieved_other_user = crud.get_focus_session(db_session, session_id=created_session.id, user_id=other_user.id)
    assert retrieved_other_user is None

    non_existent = crud.get_focus_session(db_session, session_id=99999, user_id=user.id)
    assert non_existent is None

def test_get_focus_sessions(db_session: Session):
    user1 = create_test_user(db_session, username_suffix="fsuser1")
    user2 = create_test_user(db_session, username_suffix="fsuser2")
    project1 = create_test_project(db_session, owner_id=user1.id)
    task1_user1 = create_test_task(db_session, project_id=project1.id, owner_id=user1.id)
    task2_user1 = create_test_task(db_session, project_id=project1.id, owner_id=user1.id)

    # Create sessions for user1
    fs1_user1_data = {**FOCUS_SESSION_DATA_1, "task_id": task1_user1.id, "status": schemas.FocusSessionStatus.COMPLETED}
    crud.create_focus_session(db_session, schemas.FocusSessionCreate(**fs1_user1_data), user_id=user1.id)

    fs2_user1_data = {**FOCUS_SESSION_DATA_2, "task_id": task2_user1.id, "status": schemas.FocusSessionStatus.ACTIVE}
    crud.create_focus_session(db_session, schemas.FocusSessionCreate(**fs2_user1_data), user_id=user1.id)

    # Create session for user2 (no task)
    fs_user2_data = {
        "start_time": FOCUS_SESSION_DATA_1["start_time"], "end_time": FOCUS_SESSION_DATA_1["end_time"],
        "status": FOCUS_SESSION_DATA_1["status"], "notes": FOCUS_SESSION_DATA_1["notes"]
    }
    crud.create_focus_session(db_session, schemas.FocusSessionCreate(**fs_user2_data), user_id=user2.id)


    # Get all sessions for user1
    sessions_user1 = crud.get_focus_sessions(db_session, user_id=user1.id)
    assert len(sessions_user1) == 2

    # Filter by task_id for user1
    sessions_task1 = crud.get_focus_sessions(db_session, user_id=user1.id, task_id=task1_user1.id)
    assert len(sessions_task1) == 1
    assert sessions_task1[0].task_id == task1_user1.id

    # Filter by status for user1
    sessions_completed = crud.get_focus_sessions(db_session, user_id=user1.id, status=schemas.FocusSessionStatus.COMPLETED)
    assert len(sessions_completed) == 1
    assert sessions_completed[0].status.value == schemas.FocusSessionStatus.COMPLETED.value

    sessions_active = crud.get_focus_sessions(db_session, user_id=user1.id, status=schemas.FocusSessionStatus.ACTIVE)
    assert len(sessions_active) == 1
    assert sessions_active[0].status.value == schemas.FocusSessionStatus.ACTIVE.value

    # Filter by time range for user1
    # This will fetch the one matching FOCUS_SESSION_DATA_1 start time for user1
    specific_time_sessions = crud.get_focus_sessions(db_session, user_id=user1.id,
                                                    start_time_after=FOCUS_SESSION_DATA_1["start_time"] - datetime.timedelta(seconds=1),
                                                    start_time_before=FOCUS_SESSION_DATA_1["start_time"] + datetime.timedelta(seconds=1))
    assert len(specific_time_sessions) == 1
    assert specific_time_sessions[0].task_id == task1_user1.id


def test_update_focus_session(db_session: Session):
    user = create_test_user(db_session)
    session_create_schema = schemas.FocusSessionCreate(
        start_time=FOCUS_SESSION_DATA_1["start_time"],
        status=schemas.FocusSessionStatus.ACTIVE # Start as active
    )
    db_fs = crud.create_focus_session(db_session, session_create=session_create_schema, user_id=user.id)

    update_data = schemas.FocusSessionUpdate(
        notes="Updated focus session notes.",
        status=schemas.FocusSessionStatus.PAUSED,
        end_time=NOW + datetime.timedelta(hours=2) # Example update for end_time
    )
    updated_fs = crud.update_focus_session(db_session, db_session=db_fs, session_update=update_data)

    assert updated_fs is not None
    assert updated_fs.id == db_fs.id
    assert updated_fs.notes == "Updated focus session notes."
    assert updated_fs.status.value == schemas.FocusSessionStatus.PAUSED.value
    assert updated_fs.end_time == NOW + datetime.timedelta(hours=2)
    assert updated_fs.user_id == user.id # Ensure user_id is not changed

    # Test partial update
    partial_update = schemas.FocusSessionUpdate(status=schemas.FocusSessionStatus.CANCELLED)
    partially_updated_fs = crud.update_focus_session(db_session, db_session=updated_fs, session_update=partial_update)
    assert partially_updated_fs.status.value == schemas.FocusSessionStatus.CANCELLED.value
    assert partially_updated_fs.notes == "Updated focus session notes." # Should remain


def test_delete_focus_session(db_session: Session):
    user = create_test_user(db_session)
    session_create_schema = schemas.FocusSessionCreate(**FOCUS_SESSION_DATA_1)
    created_session = crud.create_focus_session(db_session, session_create=session_create_schema, user_id=user.id)

    deleted_session = crud.delete_focus_session(db_session, session_id=created_session.id, user_id=user.id)
    assert deleted_session is not None
    assert deleted_session.id == created_session.id

    retrieved_after_delete = crud.get_focus_session(db_session, session_id=created_session.id, user_id=user.id)
    assert retrieved_after_delete is None

    # Test deleting non-existent
    non_existent_deleted = crud.delete_focus_session(db_session, session_id=99999, user_id=user.id)
    assert non_existent_deleted is None

    # Test deleting other user's session
    session_to_keep_create_schema = schemas.FocusSessionCreate(**FOCUS_SESSION_DATA_2)
    session_to_keep = crud.create_focus_session(db_session, session_create=session_to_keep_create_schema, user_id=user.id)
    other_user = create_test_user(db_session, username_suffix="otherdeletefs")
    failed_delete = crud.delete_focus_session(db_session, session_id=session_to_keep.id, user_id=other_user.id)
    assert failed_delete is None
    assert crud.get_focus_session(db_session, session_id=session_to_keep.id, user_id=user.id) is not None
