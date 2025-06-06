import pytest
from sqlalchemy.orm import Session
from app import crud, schemas, models # Assuming models are needed for asserts
from app.core.security import verify_password, get_password_hash # For testing password updates

# --- Test Data ---
USER_TEST_DATA_1 = {
    "email": "testuser1@example.com",
    "username": "testuser1",
    "password": "testpassword123",
}

USER_TEST_DATA_2 = {
    "email": "testuser2@example.com",
    "username": "testuser2",
    "password": "anotherpassword",
}

# --- Tests for User CRUD operations ---

def test_create_user(db_session: Session):
    user_in = schemas.UserCreate(**USER_TEST_DATA_1)
    db_user = crud.create_user(db_session, user_create=user_in)

    assert db_user is not None
    assert db_user.email == USER_TEST_DATA_1["email"]
    assert db_user.username == USER_TEST_DATA_1["username"]
    assert hasattr(db_user, "hashed_password")
    assert db_user.hashed_password is not None
    assert verify_password(USER_TEST_DATA_1["password"], db_user.hashed_password)
    assert db_user.id is not None
    assert db_user.is_active is True # Default value

def test_get_user(db_session: Session):
    user_in = schemas.UserCreate(**USER_TEST_DATA_1)
    created_user = crud.create_user(db_session, user_create=user_in)

    retrieved_user = crud.get_user(db_session, user_id=created_user.id)
    assert retrieved_user is not None
    assert retrieved_user.id == created_user.id
    assert retrieved_user.email == created_user.email
    assert retrieved_user.username == created_user.username

    non_existent_user = crud.get_user(db_session, user_id=99999)
    assert non_existent_user is None

def test_get_user_by_email(db_session: Session):
    user_in = schemas.UserCreate(**USER_TEST_DATA_1)
    crud.create_user(db_session, user_create=user_in)

    retrieved_user = crud.get_user_by_email(db_session, email=USER_TEST_DATA_1["email"])
    assert retrieved_user is not None
    assert retrieved_user.email == USER_TEST_DATA_1["email"]

    non_existent_user = crud.get_user_by_email(db_session, email="nonexistent@example.com")
    assert non_existent_user is None

def test_get_user_by_username(db_session: Session):
    user_in = schemas.UserCreate(**USER_TEST_DATA_1)
    crud.create_user(db_session, user_create=user_in)

    retrieved_user = crud.get_user_by_username(db_session, username=USER_TEST_DATA_1["username"])
    assert retrieved_user is not None
    assert retrieved_user.username == USER_TEST_DATA_1["username"]

    non_existent_user = crud.get_user_by_username(db_session, username="nonexistentuser")
    assert non_existent_user is None

def test_get_users(db_session: Session):
    user_in_1 = schemas.UserCreate(**USER_TEST_DATA_1)
    user_in_2 = schemas.UserCreate(**USER_TEST_DATA_2)
    crud.create_user(db_session, user_create=user_in_1)
    crud.create_user(db_session, user_create=user_in_2)

    users = crud.get_users(db_session, skip=0, limit=10)
    assert len(users) == 2

    users_limit_1 = crud.get_users(db_session, skip=0, limit=1)
    assert len(users_limit_1) == 1

    users_skip_1 = crud.get_users(db_session, skip=1, limit=10)
    assert len(users_skip_1) == 1
    # Ensure the correct user is skipped
    emails_in_users_skip_1 = {user.email for user in users_skip_1}
    assert USER_TEST_DATA_2["email"] in emails_in_users_skip_1


def test_update_user(db_session: Session):
    user_in = schemas.UserCreate(**USER_TEST_DATA_1)
    db_user = crud.create_user(db_session, user_create=user_in)

    update_data = schemas.UserUpdate(
        email="updated_email@example.com",
        username="updated_username",
        is_active=False,
        preferences={"theme": "dark"}
    )
    updated_user = crud.update_user(db_session, db_user=db_user, user_update=update_data)

    assert updated_user is not None
    assert updated_user.id == db_user.id
    assert updated_user.email == "updated_email@example.com"
    assert updated_user.username == "updated_username"
    assert updated_user.is_active is False
    assert updated_user.preferences == {"theme": "dark"}

    # Test partial update
    partial_update_data = schemas.UserUpdate(username="partial_update_user")
    partially_updated_user = crud.update_user(db_session, db_user=updated_user, user_update=partial_update_data)
    assert partially_updated_user.username == "partial_update_user"
    assert partially_updated_user.email == "updated_email@example.com" # Should remain unchanged

def test_update_password(db_session: Session):
    user_in = schemas.UserCreate(**USER_TEST_DATA_1)
    db_user = crud.create_user(db_session, user_create=user_in)

    new_password = "new_strong_password"
    # The CRUD function for updating password likely expects the new password directly,
    # and handles hashing internally. It also likely takes the user object, not a separate password_update schema.
    # Let's assume crud.update_password takes (db: Session, *, db_user: models.User, new_password: str)
    # This is a common pattern. If it takes a schema, this part needs adjustment.
    # Based on common practice, let's try sending the new password string directly.
    # The original test code used a schema `PasswordUpdate` which might not exist or be used this way by `crud.update_password`.
    # The prompt implies `crud.update_password` exists. I will assume it takes `new_password_hash` or similar.
    # Re-checking the prompt: it uses `schemas.PasswordUpdate`.
    # I'll stick to the prompt's `schemas.PasswordUpdate` for now and see if the schema exists
    # and if `crud.update_password` uses it.

    password_update_data = schemas.PasswordUpdate(
        current_password=USER_TEST_DATA_1["password"],
        new_password=new_password
    )

    # Assuming crud.update_password takes db_user and the schema for update
    # And it returns the updated user or None on failure (e.g. wrong current_password)
    updated_user = crud.update_password(db_session, db_user=db_user, password_update=password_update_data)

    assert updated_user is not None, "Password update failed, user not returned. Check current_password logic."
    assert verify_password(new_password, updated_user.hashed_password)

    # Test with incorrect current password
    incorrect_password_update = schemas.PasswordUpdate(
        current_password="wrong_current_password",
        new_password="another_new_password"
    )
    failed_update_user = crud.update_password(db_session, db_user=db_user, password_update=incorrect_password_update)
    assert failed_update_user is None # Expecting None if current_password verification fails

    # Ensure password hasn't changed to "another_new_password"
    # It should still be "new_strong_password"
    db_session.refresh(db_user) # Refresh user state from DB
    assert verify_password(new_password, db_user.hashed_password)


def test_delete_user(db_session: Session):
    user_in = schemas.UserCreate(**USER_TEST_DATA_1)
    created_user = crud.create_user(db_session, user_create=user_in)

    deleted_user = crud.delete_user(db_session, user_id=created_user.id)
    assert deleted_user is not None
    assert deleted_user.id == created_user.id

    retrieved_after_delete = crud.get_user(db_session, user_id=created_user.id)
    assert retrieved_after_delete is None

    # Test deleting non-existent user
    non_existent_deleted_user = crud.delete_user(db_session, user_id=99999)
    assert non_existent_deleted_user is None
