import datetime
from typing import List, Dict # For type hinting
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app import crud, schemas, models # Ensure models is imported for User
from app.core.config import settings # For API prefix
# app.main is not directly used by the test client usually, TestClient imports it.
# However, if fixtures need it, it's fine. Let's assume TestClient handles app loading.

# Helper to get auth headers (simplified for this subtask)
# In a real setup, this would likely be a fixture in conftest.py
def get_user_authentication_headers(client: TestClient, db: Session, email_prefix="test_monitoring") -> Dict[str, str]:
    # Generate unique user credentials for each call to ensure test isolation
    timestamp_int = int(datetime.datetime.utcnow().timestamp()) # Use integer part of timestamp
    test_username = f"{email_prefix}user{timestamp_int}" # Simpler username, no dots
    test_email = f"{email_prefix}email{timestamp_int}@example.com" # Keep email unique
    test_password = "testpassword"

    # Create the unique user
    user_in_create = schemas.UserCreate(username=test_username, email=test_email, password=test_password)
    user = crud.create_user(db=db, user_create=user_in_create)
    db.flush()  # Ensure the user data is sent to the DB within the current transaction
    db.refresh(user) # Refresh the user object to get any DB-generated values like ID

    # Optional: Add a verification step to see if the user can be fetched immediately
    fetched_user = crud.get_user_by_email(db, email=test_email)
    if not fetched_user:
        print(f"DEBUG: User {test_email} NOT found immediately after create/flush/refresh.")
    else:
        print(f"DEBUG: User {test_email} (ID: {fetched_user.id}, username: {fetched_user.username}) IS found after create/flush/refresh.")
        # Manual verification attempt
        from app.core.security import verify_password
        is_password_correct = verify_password(test_password, fetched_user.hashed_password)
        print(f"DEBUG: Manual password verify for user {fetched_user.username}: {is_password_correct}")
        if not is_password_correct:
            # This would be a major issue with password hashing/verification itself
            print(f"DEBUG: Hashed password in DB: {fetched_user.hashed_password}")


    login_data = {
        "username": test_username, # Use the generated unique username
        "password": test_password,
    }
    # Construct the URL using the correct API prefix based on main.py
    # auth router is at /api/auth
    api_auth_prefix = "/api/auth"
    auth_url = f"{api_auth_prefix}/token" # Assuming /token is the endpoint in auth router

    r = client.post(auth_url, data=login_data)
    response_json = r.json()
    if r.status_code != 200:
        # Attempt to provide more context if user creation/login failed
        print(f"Auth Debug: User email used: {test_email}") # Corrected variable name
        print(f"Auth Debug: Login data sent: {login_data}")
        print(f"Auth Debug: Response status: {r.status_code}")
        print(f"Auth Debug: Response content: {r.text}")
    assert r.status_code == 200, f"Failed to authenticate: {response_json}"
    token = response_json["access_token"]
    return {"Authorization": f"Bearer {token}"}, user # Return user for cleanup

# Test function, assumes 'client' and 'db_session' fixtures are provided by conftest.py
def test_get_energy_logs_date_range_filter(client: TestClient, db_session: Session) -> None:
    headers, test_user = get_user_authentication_headers(client, db_session)

    # Timestamps for testing
    now = datetime.datetime.utcnow()
    day_minus_2_start = (now - datetime.timedelta(days=2)).replace(hour=0, minute=0, second=0, microsecond=0)
    day_minus_1_morning = (now - datetime.timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)
    day_minus_1_evening = (now - datetime.timedelta(days=1)).replace(hour=20, minute=0, second=0, microsecond=0)
    today_morning = now.replace(hour=9, minute=0, second=0, microsecond=0)
    # Ensure today_evening is distinct from today_morning if 'now' is close to 9 AM
    if now.hour == 9 and now.minute == 0:
        today_evening = now.replace(hour=22, minute=0, second=0, microsecond=0)
    else:
        today_evening = now.replace(hour=22, minute=0, second=0, microsecond=0)

    day_plus_1_start = (now + datetime.timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)

    logs_to_create = [
        schemas.EnergyLogCreate(timestamp=day_minus_2_start, energy_level=schemas.EnergyLevel.LOW, notes="Two days ago, start"),
        schemas.EnergyLogCreate(timestamp=day_minus_1_morning, energy_level=schemas.EnergyLevel.MEDIUM, notes="Yesterday morning"),
        schemas.EnergyLogCreate(timestamp=day_minus_1_evening, energy_level=schemas.EnergyLevel.HIGH, notes="Yesterday evening"),
        schemas.EnergyLogCreate(timestamp=today_morning, energy_level=schemas.EnergyLevel.VERY_HIGH, notes="Today morning"),
        schemas.EnergyLogCreate(timestamp=today_evening, energy_level=schemas.EnergyLevel.MEDIUM, notes="Today evening"),
        schemas.EnergyLogCreate(timestamp=day_plus_1_start, energy_level=schemas.EnergyLevel.LOW, notes="Tomorrow start"),
    ]

    created_log_ids = []
    for log_in in logs_to_create:
        db_log = crud.create_energy_log(db=db_session, log_create=log_in, user_id=test_user.id) # Corrected parameter name
        created_log_ids.append(db_log.id)

    date_start_param = day_minus_1_morning.date().isoformat()
    date_end_param = today_morning.date().isoformat()

    expected_notes_in_response = [
        "Yesterday morning", "Yesterday evening", "Today morning", "Today evening"
    ]

    # Construct the URL for energy logs
    # monitoring router is at /api/monitoring (if active)
    api_monitoring_prefix = "/api/monitoring"
    energy_logs_url = f"{api_monitoring_prefix}/energy-logs"

    response = client.get(
        energy_logs_url,
        headers=headers,
        params={"date_start": date_start_param, "date_end": date_end_param}
    )

    assert response.status_code == 200, f"API call failed: {response.text}"
    response_data = response.json()
    assert len(response_data) == len(expected_notes_in_response), \
        f"Expected {len(expected_notes_in_response)} logs, got {len(response_data)}. Response: {response_data}"

    returned_notes = sorted([log['notes'] for log in response_data])
    assert returned_notes == sorted(expected_notes_in_response), \
        f"Returned logs do not match expected. Got: {returned_notes}, Expected: {sorted(expected_notes_in_response)}"

    # Teardown: Delete created energy logs
    for log_id in created_log_ids:
        crud.delete_energy_log(db=db_session, log_id=log_id, user_id=test_user.id)

    # Teardown: Delete created user
    # Ensure this user is specific to this test and not used elsewhere, or manage cleanup carefully
    # crud.delete_user(db=db_session, user_id=test_user.id) # Commented out for safety, enable if appropriate
