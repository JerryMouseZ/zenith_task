import pytest
from sqlalchemy.orm import Session
from app import crud, schemas, models
import datetime
import time

# Helper function to create a dummy user
def create_test_user(db_session: Session, username_suffix="energytestuser") -> models.User:
    email = f"{username_suffix}{time.time_ns()}@example.com"
    username = f"{username_suffix}{time.time_ns()}"
    user_in = schemas.UserCreate(email=email, username=username, password="elpassword")
    return crud.create_user(db_session, user_create=user_in)

# --- Test Data ---
TIMESTAMP_NOW = datetime.datetime.utcnow()

ENERGY_LOG_DATA_1 = {
    "timestamp": TIMESTAMP_NOW,
    "energy_level": schemas.EnergyLevel.HIGH,
    "notes": "Feeling energetic after a good sleep."
}

ENERGY_LOG_DATA_2 = {
    "timestamp": TIMESTAMP_NOW - datetime.timedelta(days=1),
    "energy_level": schemas.EnergyLevel.LOW,
    "notes": "Tired yesterday evening."
}

# --- Tests for EnergyLog CRUD operations ---

def test_create_energy_log(db_session: Session):
    user = create_test_user(db_session)
    log_in = schemas.EnergyLogCreate(**ENERGY_LOG_DATA_1)

    db_log = crud.create_energy_log(db_session, log_create=log_in, user_id=user.id)

    assert db_log is not None
    assert db_log.user_id == user.id
    # Compare timestamps with tolerance for minor precision differences if necessary
    assert abs(db_log.timestamp - ENERGY_LOG_DATA_1["timestamp"]) < datetime.timedelta(seconds=1)
    assert db_log.energy_level.value == schemas.EnergyLevel.HIGH.value
    assert db_log.notes == ENERGY_LOG_DATA_1["notes"]
    assert db_log.id is not None


def test_get_energy_log(db_session: Session):
    user = create_test_user(db_session)
    log_in = schemas.EnergyLogCreate(**ENERGY_LOG_DATA_1)
    created_log = crud.create_energy_log(db_session, log_create=log_in, user_id=user.id)

    retrieved_log = crud.get_energy_log(db_session, log_id=created_log.id, user_id=user.id)
    assert retrieved_log is not None
    assert retrieved_log.id == created_log.id
    assert retrieved_log.user_id == user.id

    # Test get for a different user (should be None)
    other_user = create_test_user(db_session, username_suffix="othereluser")
    retrieved_other_user = crud.get_energy_log(db_session, log_id=created_log.id, user_id=other_user.id)
    assert retrieved_other_user is None

    non_existent = crud.get_energy_log(db_session, log_id=99999, user_id=user.id)
    assert non_existent is None


def test_get_energy_logs(db_session: Session):
    user1 = create_test_user(db_session, username_suffix="eluser1")
    user2 = create_test_user(db_session, username_suffix="eluser2")

    # Create logs for user1 ensuring timestamps are distinct for reliable time filtering
    log1_user1_ts = TIMESTAMP_NOW - datetime.timedelta(hours=2)
    log2_user1_ts = TIMESTAMP_NOW - datetime.timedelta(hours=1)

    crud.create_energy_log(db_session, schemas.EnergyLogCreate(timestamp=log1_user1_ts, energy_level=schemas.EnergyLevel.HIGH, notes="Log1 U1"), user_id=user1.id)
    crud.create_energy_log(db_session, schemas.EnergyLogCreate(timestamp=log2_user1_ts, energy_level=schemas.EnergyLevel.LOW, notes="Log2 U1"), user_id=user1.id)

    # Create log for user2
    crud.create_energy_log(db_session, schemas.EnergyLogCreate(**ENERGY_LOG_DATA_1), user_id=user2.id)

    # Get all logs for user1
    logs_user1 = crud.get_energy_logs(db_session, user_id=user1.id)
    assert len(logs_user1) == 2

    # Filter by energy_level for user1
    logs_high_energy = crud.get_energy_logs(db_session, user_id=user1.id, energy_level=schemas.EnergyLevel.HIGH)
    assert len(logs_high_energy) == 1
    assert logs_high_energy[0].energy_level.value == schemas.EnergyLevel.HIGH.value

    logs_low_energy = crud.get_energy_logs(db_session, user_id=user1.id, energy_level=schemas.EnergyLevel.LOW)
    assert len(logs_low_energy) == 1
    assert logs_low_energy[0].energy_level.value == schemas.EnergyLevel.LOW.value

    # Filter by time range to fetch only log2_user1
    time_filter_start = log2_user1_ts - datetime.timedelta(minutes=1)
    time_filter_end = log2_user1_ts + datetime.timedelta(minutes=1)
    logs_in_time = crud.get_energy_logs(db_session, user_id=user1.id, timestamp_after=time_filter_start, timestamp_before=time_filter_end)
    assert len(logs_in_time) == 1
    assert abs(logs_in_time[0].timestamp - log2_user1_ts) < datetime.timedelta(seconds=1)
    assert logs_in_time[0].energy_level.value == schemas.EnergyLevel.LOW.value


def test_update_energy_log(db_session: Session):
    user = create_test_user(db_session)
    log_in = schemas.EnergyLogCreate(**ENERGY_LOG_DATA_1)
    db_el = crud.create_energy_log(db_session, log_create=log_in, user_id=user.id)

    update_data = schemas.EnergyLogUpdate(
        notes="Feeling very sleepy now.",
        energy_level=schemas.EnergyLevel.VERY_LOW
    )
    updated_el = crud.update_energy_log(db_session, db_log=db_el, log_update=update_data)

    assert updated_el is not None
    assert updated_el.id == db_el.id
    assert updated_el.notes == "Feeling very sleepy now."
    assert updated_el.energy_level.value == schemas.EnergyLevel.VERY_LOW.value
    assert updated_el.user_id == user.id

    # Test partial update
    partial_update = schemas.EnergyLogUpdate(notes="Just a bit tired.")
    partially_updated_el = crud.update_energy_log(db_session, db_log=updated_el, log_update=partial_update)
    assert partially_updated_el.notes == "Just a bit tired."
    assert partially_updated_el.energy_level.value == schemas.EnergyLevel.VERY_LOW.value # Should remain


def test_delete_energy_log(db_session: Session):
    user = create_test_user(db_session)
    log_in = schemas.EnergyLogCreate(**ENERGY_LOG_DATA_1)
    created_log = crud.create_energy_log(db_session, log_create=log_in, user_id=user.id)

    deleted_log = crud.delete_energy_log(db_session, log_id=created_log.id, user_id=user.id)
    assert deleted_log is not None
    assert deleted_log.id == created_log.id

    retrieved_after_delete = crud.get_energy_log(db_session, log_id=created_log.id, user_id=user.id)
    assert retrieved_after_delete is None

    # Test deleting non-existent
    non_existent_deleted = crud.delete_energy_log(db_session, log_id=99999, user_id=user.id)
    assert non_existent_deleted is None

    # Test deleting other user's log
    log_in_2 = schemas.EnergyLogCreate(**ENERGY_LOG_DATA_2) # Ensure different data if needed
    log_to_keep = crud.create_energy_log(db_session, log_create=log_in_2, user_id=user.id)
    other_user = create_test_user(db_session, username_suffix="otherdeleteel")
    failed_delete = crud.delete_energy_log(db_session, log_id=log_to_keep.id, user_id=other_user.id)
    assert failed_delete is None
    assert crud.get_energy_log(db_session, log_id=log_to_keep.id, user_id=user.id) is not None
