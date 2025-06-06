import pytest
from sqlalchemy.orm import Session
from app import crud, schemas, models
import time # For unique name generation

# Helper function to create a dummy user
def create_test_user(db_session: Session, email_suffix="taguser.example.com", username_suffix="tagtestuser") -> models.User:
    # Ensure unique email and username for each call
    unique_part = f"{time.time_ns()}"
    email = f"{username_suffix}{unique_part}@{email_suffix.split('@')[-1]}"
    username = f"{username_suffix}{unique_part}"
    user_in = schemas.UserCreate(email=email, username=username, password="tagpassword")
    return crud.create_user(db_session, user_create=user_in)

# --- Test Data ---
TAG_TEST_DATA_1 = {
    "name": "Urgent",
    "color": "#FF0000", # Red
}

TAG_TEST_DATA_2 = {
    "name": "Work",
    "color": "#0000FF", # Blue
}

# --- Tests for Tag CRUD operations ---

def test_create_tag(db_session: Session):
    user = create_test_user(db_session)
    tag_in_data = {**TAG_TEST_DATA_1}
    # Ensure unique name for this test run if TAG_TEST_DATA_1["name"] is static
    tag_in_data["name"] = f"{TAG_TEST_DATA_1['name']}_{time.time_ns()}"
    tag_in = schemas.TagCreate(**tag_in_data)

    db_tag = crud.create_tag(db_session, tag_create=tag_in, user_id=user.id)

    assert db_tag is not None
    assert db_tag.name == tag_in.name
    assert db_tag.color == TAG_TEST_DATA_1["color"]
    assert db_tag.user_id == user.id
    assert db_tag.id is not None

    # Test creating tag with the same name for the same user (should fail)
    # crud.create_tag raises ValueError for duplicate name as per its implementation
    with pytest.raises(ValueError, match="Tag with this name already exists for this user."):
        crud.create_tag(db_session, tag_create=tag_in, user_id=user.id)

    # Test creating tag with the same name for a different user (should succeed)
    other_user = create_test_user(db_session, username_suffix="othertaguser")
    # We use the same tag_in object which has the unique name generated for 'user'
    # This means the name is globally unique due to the timestamp, so it will succeed for other_user.
    # If we wanted to test (other_user, "static_name") vs (user, "static_name"),
    # the unique name generation would need to be inside the specific test case logic.
    # For now, this is fine as it tests that other_user can have a tag that happens to have the same name string.
    db_tag_other_user = crud.create_tag(db_session, tag_create=tag_in, user_id=other_user.id)
    assert db_tag_other_user is not None
    assert db_tag_other_user.name == tag_in.name # Name is same due to tag_in reuse
    assert db_tag_other_user.user_id == other_user.id


def test_get_tag(db_session: Session):
    user = create_test_user(db_session)
    tag_name = f"GettableTag_{time.time_ns()}"
    tag_in = schemas.TagCreate(name=tag_name, color=TAG_TEST_DATA_1["color"])
    created_tag = crud.create_tag(db_session, tag_create=tag_in, user_id=user.id)

    # Test get by owner
    retrieved_tag = crud.get_tag(db_session, tag_id=created_tag.id, user_id=user.id)
    assert retrieved_tag is not None
    assert retrieved_tag.id == created_tag.id
    assert retrieved_tag.name == tag_name

    # Test get for a different user (should be None)
    other_user = create_test_user(db_session, username_suffix="othergettaguser")
    retrieved_tag_other_user = crud.get_tag(db_session, tag_id=created_tag.id, user_id=other_user.id)
    assert retrieved_tag_other_user is None

    non_existent_tag = crud.get_tag(db_session, tag_id=99999, user_id=user.id)
    assert non_existent_tag is None

def test_get_tag_by_name(db_session: Session):
    user = create_test_user(db_session)
    tag_name = f"NamedTag_{time.time_ns()}"
    tag_in = schemas.TagCreate(name=tag_name, color=TAG_TEST_DATA_1["color"])
    crud.create_tag(db_session, tag_create=tag_in, user_id=user.id)

    retrieved_tag = crud.get_tag_by_name(db_session, name=tag_name, user_id=user.id)
    assert retrieved_tag is not None
    assert retrieved_tag.name == tag_name
    assert retrieved_tag.user_id == user.id

    # Test get non-existent name
    non_existent_tag = crud.get_tag_by_name(db_session, name="NonExistentTagName", user_id=user.id)
    assert non_existent_tag is None

    # Test get tag by name for a different user (should be None)
    other_user = create_test_user(db_session, username_suffix="othernamedtaguser")
    retrieved_tag_other_user = crud.get_tag_by_name(db_session, name=tag_name, user_id=other_user.id)
    assert retrieved_tag_other_user is None


def test_get_tags_by_user(db_session: Session):
    user1 = create_test_user(db_session, username_suffix="user1tags")
    user2 = create_test_user(db_session, username_suffix="user2tags")

    tag1_u1_name = f"Tag1U1_{time.time_ns()}"
    tag2_u1_name = f"Tag2U1_{time.time_ns()}"
    crud.create_tag(db_session, schemas.TagCreate(name=tag1_u1_name, color="#111111"), user_id=user1.id)
    crud.create_tag(db_session, schemas.TagCreate(name=tag2_u1_name, color="#222222"), user_id=user1.id)
    crud.create_tag(db_session, schemas.TagCreate(name=f"Tag1U2_{time.time_ns()}", color="#333333"), user_id=user2.id)

    tags_user1 = crud.get_tags_by_user(db_session, user_id=user1.id)
    assert len(tags_user1) == 2

    tags_user2 = crud.get_tags_by_user(db_session, user_id=user2.id)
    assert len(tags_user2) == 1

    # Test pagination
    tags_user1_limit1 = crud.get_tags_by_user(db_session, user_id=user1.id, limit=1)
    assert len(tags_user1_limit1) == 1

    # Assuming default order is by ID or creation time, the skipped one will be the other.
    tags_user1_skip1 = crud.get_tags_by_user(db_session, user_id=user1.id, skip=1, limit=1)
    assert len(tags_user1_skip1) == 1
    assert tags_user1_limit1[0].name != tags_user1_skip1[0].name


def test_update_tag(db_session: Session):
    user = create_test_user(db_session)
    original_name = f"OriginalTag_{time.time_ns()}"
    tag_in = schemas.TagCreate(name=original_name, color=TAG_TEST_DATA_1["color"])
    db_tag = crud.create_tag(db_session, tag_create=tag_in, user_id=user.id)

    updated_name = f"UpdatedName_{time.time_ns()}"
    update_data = schemas.TagUpdate(
        name=updated_name,
        color="#00FF00" # Green
    )
    updated_tag = crud.update_tag(db_session, db_tag=db_tag, tag_update=update_data, user_id=user.id)

    assert updated_tag is not None
    assert updated_tag.id == db_tag.id
    assert updated_tag.name == updated_name
    assert updated_tag.color == "#00FF00"
    assert updated_tag.user_id == user.id

    # Test partial update (only color)
    partial_update_data = schemas.TagUpdate(color="#AAAAAA")
    partially_updated_tag = crud.update_tag(db_session, db_tag=updated_tag, tag_update=partial_update_data, user_id=user.id)
    assert partially_updated_tag.name == updated_name # Should remain from previous update
    assert partially_updated_tag.color == "#AAAAAA"

    # Test updating name to an existing tag name of the same user (should fail)
    existing_tag_name = f"ExistingName_{time.time_ns()}"
    crud.create_tag(db_session, schemas.TagCreate(name=existing_tag_name, color="#CCCCCC"), user_id=user.id)

    fail_update_data = schemas.TagUpdate(name=existing_tag_name)
    with pytest.raises(ValueError, match="Another tag with this name already exists for this user."):
        crud.update_tag(db_session, db_tag=partially_updated_tag, tag_update=fail_update_data, user_id=user.id)

    # Test updating name to an existing tag name of *another* user (should succeed)
    other_user = create_test_user(db_session, username_suffix="otherupdatetag")
    other_user_tag_name = f"OtherUserTag_{time.time_ns()}"
    crud.create_tag(db_session, schemas.TagCreate(name=other_user_tag_name, color="#DDDDDD"), user_id=other_user.id)

    update_to_other_user_name_data = schemas.TagUpdate(name=other_user_tag_name)
    successful_update = crud.update_tag(db_session, db_tag=partially_updated_tag, tag_update=update_to_other_user_name_data, user_id=user.id)
    assert successful_update.name == other_user_tag_name


def test_delete_tag(db_session: Session):
    user = create_test_user(db_session)
    tag_name = f"DeletableTag_{time.time_ns()}"
    tag_in = schemas.TagCreate(name=tag_name, color=TAG_TEST_DATA_1["color"])
    created_tag = crud.create_tag(db_session, tag_create=tag_in, user_id=user.id)

    # Test deletion by owner
    deleted_tag = crud.delete_tag(db_session, tag_id=created_tag.id, user_id=user.id)
    assert deleted_tag is not None
    assert deleted_tag.id == created_tag.id

    retrieved_after_delete = crud.get_tag(db_session, tag_id=created_tag.id, user_id=user.id)
    assert retrieved_after_delete is None

    # Test deleting non-existent tag
    non_existent_deleted_tag = crud.delete_tag(db_session, tag_id=99999, user_id=user.id)
    assert non_existent_deleted_tag is None

    # Test attempting to delete tag owned by another user
    tag_to_keep_name = f"KeptTag_{time.time_ns()}"
    tag_to_keep = crud.create_tag(db_session, schemas.TagCreate(name=tag_to_keep_name, color="#EEEEEE"), user_id=user.id) # Added color
    other_user = create_test_user(db_session, username_suffix="otherdeletetaguser")

    failed_delete_attempt = crud.delete_tag(db_session, tag_id=tag_to_keep.id, user_id=other_user.id)
    assert failed_delete_attempt is None
    assert crud.get_tag(db_session, tag_id=tag_to_keep.id, user_id=user.id) is not None
