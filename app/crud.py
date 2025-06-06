# Functions for CRUD operations
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional, Type, TypeVar
from . import models, schemas
from .core.security import get_password_hash, verify_password # Added verify_password
import datetime

# Generic helper for updating a model instance
ModelType = TypeVar("ModelType", bound=models.Base)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=schemas.BaseModel)

def update_db_object(db_obj: ModelType, updates: UpdateSchemaType) -> ModelType:
    update_data = updates.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_obj, key, value)
    return db_obj

# --- User CRUD operations ---
def get_user(db: Session, user_id: int) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.email == email).first()

def get_user_by_username(db: Session, username: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.username == username).first()

def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[models.User]: # Make sure this is not duplicated or is the correct one
    return db.query(models.User).offset(skip).limit(limit).all()

def create_user(db: Session, user_create: schemas.UserCreate) -> models.User:
    hashed_password = get_password_hash(user_create.password)
    db_user = models.User(
        email=user_create.email,
        username=user_create.username,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user(db: Session, db_user: models.User, user_update: schemas.UserUpdate) -> models.User:
    db_user = update_db_object(db_user, user_update)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_password(db: Session, db_user: models.User, password_update: schemas.PasswordUpdate) -> Optional[models.User]:
    if not verify_password(password_update.current_password, db_user.hashed_password):
        return None # Current password incorrect
    new_hashed_password = get_password_hash(password_update.new_password)
    db_user.hashed_password = new_hashed_password
    db_user.updated_at = datetime.datetime.utcnow()
    db.commit()
    db.refresh(db_user)
    return db_user

def delete_user(db: Session, user_id: int) -> Optional[models.User]:
    db_user = get_user(db, user_id)
    if db_user:
        db.delete(db_user)
        db.commit()
    return db_user

# --- Project CRUD operations ---
def get_project(db: Session, project_id: int, user_id: Optional[int] = None) -> Optional[models.Project]:
    query = db.query(models.Project).filter(models.Project.id == project_id)
    if user_id is not None: # Filter by owner if user_id is provided
        query = query.filter(models.Project.owner_id == user_id)
    return query.first()

# Removed duplicated get_projects_by_user. This is the correct one.
def get_projects_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 100, archived: Optional[bool] = None) -> List[models.Project]:
    query = db.query(models.Project).filter(models.Project.owner_id == user_id)
    if archived is not None:
        query = query.filter(models.Project.is_archived == archived)
    return query.offset(skip).limit(limit).all()

def create_project(db: Session, project_create: schemas.ProjectCreate, owner_id: int) -> models.Project:
    db_project_data = project_create.dict()

    # Ensure is_archived defaults to False if not provided
    is_archived = db_project_data.get("is_archived", False)
    db_project_data["is_archived"] = is_archived

    if is_archived:
        # If archived_at is not provided with is_archived=True, set it.
        if not db_project_data.get("archived_at"):
            db_project_data["archived_at"] = datetime.datetime.utcnow()
    else:
        # If not archived, ensure archived_at is None.
        db_project_data["archived_at"] = None

    db_project = models.Project(**db_project_data, owner_id=owner_id)
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project

def update_project(db: Session, db_project: models.Project, project_update: schemas.ProjectUpdate) -> models.Project:
    update_data = project_update.dict(exclude_unset=True)

    # Apply all updates first
    for key, value in update_data.items():
        setattr(db_project, key, value)

    # Specific logic if is_archived was part of the update
    if 'is_archived' in update_data:
        if db_project.is_archived:
            # If is_archived is True, and archived_at was not set or set to None by the update, set it now.
            if db_project.archived_at is None:
                db_project.archived_at = datetime.datetime.utcnow()
        else:
            # If is_archived is False, ensure archived_at is None.
            db_project.archived_at = None

    db.commit()
    db.refresh(db_project)
    return db_project

def delete_project(db: Session, project_id: int, user_id: int) -> Optional[models.Project]:
    # Ensure user owns the project before deleting
    db_project = db.query(models.Project).filter(models.Project.id == project_id, models.Project.owner_id == user_id).first()
    if db_project:
        db.delete(db_project) # Tasks associated might be deleted due to cascade in model
        db.commit()
    return db_project

# --- Task CRUD operations ---
def get_task(db: Session, task_id: int, user_id: Optional[int] = None) -> Optional[models.Task]:
    """ Gets a specific task. If user_id is provided, it ensures the task belongs to a project owned by the user. """
    query = db.query(models.Task).filter(models.Task.id == task_id)
    if user_id is not None:
        query = query.join(models.Project).filter(models.Project.owner_id == user_id)
    return query.first()

def get_tasks(
    db: Session,
    user_id: int, # Assuming tasks are always fetched in the context of a user
    project_id: Optional[int] = None,
    completed: Optional[bool] = None,
    due_date_before: Optional[datetime.datetime] = None,
    due_date_after: Optional[datetime.datetime] = None,
    priority: Optional[int] = None,
    skip: int = 0,
    limit: int = 100
) -> List[models.Task]:
    query = db.query(models.Task).join(models.Project).filter(models.Project.owner_id == user_id)
    if project_id is not None:
        query = query.filter(models.Task.project_id == project_id)
    if completed is not None:
        query = query.filter(models.Task.completed == completed)
    if due_date_before is not None:
        query = query.filter(models.Task.due_date <= due_date_before)
    if due_date_after is not None:
        query = query.filter(models.Task.due_date >= due_date_after)
    if priority is not None:
        query = query.filter(models.Task.priority == priority)
    # Add parent_task_id filter if that feature is implemented in models.Task
    # if parent_task_id is not None:
    #     query = query.filter(models.Task.parent_id == parent_task_id)
    if parent_task_id is not None: # New filter
        query = query.filter(models.Task.parent_task_id == parent_task_id)
    if is_recurring is not None: # New filter
        query = query.filter(models.Task.is_recurring == is_recurring)
    if tags: # New filter for tags (list of tag IDs)
        # This ensures task has AT LEAST ONE of the provided tags.
        # If task must have ALL tags, a different approach with multiple joins or subqueries would be needed.
        query = query.join(models.Task.tags).filter(models.Tag.id.in_(tags)).distinct()

    return query.order_by(models.Task.order_in_list.asc(), models.Task.priority.desc(), models.Task.due_date.asc(), models.Task.created_at.asc()).offset(skip).limit(limit).all()


def create_task(db: Session, task_create: schemas.TaskCreate) -> models.Task:
    # project_id is now part of task_create and should be validated if necessary by the caller or here
    # assignee_id is also part of task_create
    # parent_task_id, order_in_list, is_recurring, recurring_schedule are also in task_create
    db_task_data = task_create.dict()

    # Ensure project_id is present, as it's required by model. TaskCreate schema requires it.
    if db_task_data.get("project_id") is None:
        raise ValueError("project_id is required to create a task")

    db_task = models.Task(**db_task_data)
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

def update_task(db: Session, db_task: models.Task, task_update: schemas.TaskUpdate) -> models.Task:
    db_task = update_db_object(db_task, task_update)
    db.commit()
    db.refresh(db_task)
    return db_task

def delete_task(db: Session, task_id: int, user_id: int) -> Optional[models.Task]:
    # Ensure user has rights to delete this task (e.g. owns the project task belongs to)
    db_task = get_task(db, task_id, user_id=user_id)
    if db_task:
        db.delete(db_task)
        db.commit()
    return db_task

# Task reordering logic placeholder - this is complex and depends on specific model fields (e.g., an 'order' field)
# def reorder_task(db: Session, task_id: int, new_order: int, user_id: int):
#     # Fetch task and verify ownership
#     # Update its order field or linked-list pointers
#     # Potentially update order of other tasks in the same list/project
#     pass

def reorder_tasks(db: Session, reorder_items: List[schemas.TaskReorderItem], user_id: int) -> List[models.Task]:
    updated_tasks = []
    task_ids_to_fetch = [item.task_id for item in reorder_items]

    # Fetch all tasks to be modified in one query if possible, though ownership check is per task.
    # For simplicity, fetch one by one to include ownership check via get_task.
    # In a high-performance scenario, batch fetching and then filtering could be an option.

    for item in reorder_items:
        db_task = get_task(db, task_id=item.task_id, user_id=user_id)
        if not db_task:
            # Or collect errors and raise a single HTTPException
            raise Exception(f"Task with id {item.task_id} not found or user does not have access.") # Should be specific HTTP Exception in router

        if item.new_order_in_list is not None:
            db_task.order_in_list = item.new_order_in_list

        if item.new_status is not None:
            # Assuming new_status maps to 'completed'.
            # This logic might need to be more sophisticated if 'new_status' means other states.
            if item.new_status.lower() == "completed":
                db_task.completed = True
            elif item.new_status.lower() == "pending": # Example for "pending"
                db_task.completed = False
            # Add more status mappings if necessary, or adjust Task model for a string status field.

        if item.new_project_id is not None and item.new_project_id != db_task.project_id:
            # Verify user has access to the new project
            db_project = get_project(db, project_id=item.new_project_id, user_id=user_id)
            if not db_project:
                raise Exception(f"Project with id {item.new_project_id} not found or user does not have access.") # Specific HTTP Exception in router
            db_task.project_id = item.new_project_id
            # When moving projects, parent_task_id might need to be cleared if the parent is in a different project,
            # or this operation should be disallowed. For now, we allow moving.
            # If parent was in old project, parent_task_id might become invalid contextually.
            # Consider clearing parent_task_id if project changes:
            # db_task.parent_task_id = None

        db.add(db_task) # Add to session, changes will be part of the commit
        updated_tasks.append(db_task)

    db.commit()
    for task in updated_tasks: # Refresh each task to get updated state from DB if needed by caller
        db.refresh(task)

    return updated_tasks


# --- Tag CRUD operations ---
def get_tag(db: Session, tag_id: int, user_id: int) -> Optional[models.Tag]:
    return db.query(models.Tag).filter(models.Tag.id == tag_id, models.Tag.user_id == user_id).first()

def get_tag_by_name(db: Session, name: str, user_id: int) -> Optional[models.Tag]:
    return db.query(models.Tag).filter(models.Tag.name == name, models.Tag.user_id == user_id).first()

def get_tags_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[models.Tag]:
    return db.query(models.Tag).filter(models.Tag.user_id == user_id).offset(skip).limit(limit).all()

def create_tag(db: Session, tag_create: schemas.TagCreate, user_id: int) -> models.Tag:
    existing_tag = get_tag_by_name(db, name=tag_create.name, user_id=user_id)
    if existing_tag:
        # This should be handled by the router to return a proper HTTP_400_BAD_REQUEST
        raise ValueError("Tag with this name already exists for this user.")
    db_tag_data = tag_create.dict()
    db_tag = models.Tag(**db_tag_data, user_id=user_id)
    db.add(db_tag)
    db.commit()
    db.refresh(db_tag)
    return db_tag

def update_tag(db: Session, db_tag: models.Tag, tag_update: schemas.TagUpdate, user_id: int) -> models.Tag:
    # Ensure db_tag belongs to the user_id; router should do this before calling.
    if db_tag.user_id != user_id:
        # This check is a safeguard. Router should prevent this.
        raise ValueError("Tag does not belong to the current user.")

    update_data = tag_update.dict(exclude_unset=True)
    if "name" in update_data and update_data["name"] != db_tag.name:
        existing_tag_with_new_name = get_tag_by_name(db, name=update_data["name"], user_id=user_id)
        if existing_tag_with_new_name and existing_tag_with_new_name.id != db_tag.id:
            raise ValueError("Another tag with this name already exists for this user.")

    db_tag = update_db_object(db_tag, tag_update) # Pass the original tag_update
    db.commit()
    db.refresh(db_tag)
    return db_tag

def delete_tag(db: Session, tag_id: int, user_id: int) -> Optional[models.Tag]:
    # Fetch the tag by id and user_id to ensure ownership before deleting
    db_tag = get_tag(db, tag_id=tag_id, user_id=user_id)
    if db_tag:
        db.delete(db_tag)
        db.commit()
    return db_tag

# --- TaskTag Association CRUD ---
def add_tag_to_task(db: Session, task_id: int, tag_id: int, user_id: int) -> Optional[models.Task]:
    db_task = get_task(db, task_id, user_id=user_id) # Check ownership of task
    db_tag = get_tag(db, tag_id=tag_id, user_id=user_id) # Check ownership of tag, and that it exists for this user
    if db_task and db_tag:
        if db_tag not in db_task.tags: # Avoid duplicates
            db_task.tags.append(db_tag)
            db.commit()
            db.refresh(db_task)
        return db_task
    return None

def remove_tag_from_task(db: Session, task_id: int, tag_id: int, user_id: int) -> Optional[models.Task]:
    db_task = get_task(db, task_id, user_id=user_id) # Check ownership of task
    db_tag = get_tag(db, tag_id=tag_id, user_id=user_id) # Check ownership of tag
    if db_task and db_tag:
        if db_tag in db_task.tags:
            db_task.tags.remove(db_tag)
            db.commit()
            db.refresh(db_task)
        return db_task
    return None

def get_tags_for_task(db: Session, task_id: int, user_id: int) -> List[models.Tag]:
    db_task = get_task(db, task_id, user_id=user_id) # Check ownership
    if db_task:
        return db_task.tags
    return []

# --- FocusSession CRUD operations ---
def get_focus_session(db: Session, session_id: int, user_id: int) -> Optional[models.FocusSession]:
    return db.query(models.FocusSession).filter(
        models.FocusSession.id == session_id,
        models.FocusSession.user_id == user_id
    ).first()

def get_focus_sessions(
    db: Session,
    user_id: int,
    task_id: Optional[int] = None,
    status: Optional[schemas.FocusSessionStatus] = None,
    start_time_after: Optional[datetime.datetime] = None,
    start_time_before: Optional[datetime.datetime] = None,
    skip: int = 0,
    limit: int = 100
) -> List[models.FocusSession]:
    query = db.query(models.FocusSession).filter(models.FocusSession.user_id == user_id)
    if task_id is not None:
        query = query.filter(models.FocusSession.task_id == task_id)
    if status is not None:
        query = query.filter(models.FocusSession.status == status)
    if start_time_after is not None:
        query = query.filter(models.FocusSession.start_time >= start_time_after)
    if start_time_before is not None:
        query = query.filter(models.FocusSession.start_time <= start_time_before)
    return query.order_by(models.FocusSession.start_time.desc()).offset(skip).limit(limit).all()

def create_focus_session(db: Session, session_create: schemas.FocusSessionCreate, user_id: int) -> models.FocusSession:
    db_session = models.FocusSession(**session_create.dict(), user_id=user_id)
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session

def update_focus_session(db: Session, db_session: models.FocusSession, session_update: schemas.FocusSessionUpdate) -> models.FocusSession:
    db_session = update_db_object(db_session, session_update)
    db.commit()
    db.refresh(db_session)
    return db_session

def delete_focus_session(db: Session, session_id: int, user_id: int) -> Optional[models.FocusSession]:
    db_session = get_focus_session(db, session_id, user_id)
    if db_session:
        db.delete(db_session)
        db.commit()
    return db_session

# --- EnergyLog CRUD operations ---
def get_energy_log(db: Session, log_id: int, user_id: int) -> Optional[models.EnergyLog]:
    return db.query(models.EnergyLog).filter(
        models.EnergyLog.id == log_id,
        models.EnergyLog.user_id == user_id
    ).first()

def get_energy_logs(
    db: Session,
    user_id: int,
    energy_level: Optional[schemas.EnergyLevel] = None,
    timestamp_after: Optional[datetime.datetime] = None,
    timestamp_before: Optional[datetime.datetime] = None,
    skip: int = 0,
    limit: int = 100
) -> List[models.EnergyLog]:
    query = db.query(models.EnergyLog).filter(models.EnergyLog.user_id == user_id)
    if energy_level is not None:
        query = query.filter(models.EnergyLog.energy_level == energy_level)
    if timestamp_after is not None:
        query = query.filter(models.EnergyLog.timestamp >= timestamp_after)
    if timestamp_before is not None:
        query = query.filter(models.EnergyLog.timestamp <= timestamp_before)
    return query.order_by(models.EnergyLog.timestamp.desc()).offset(skip).limit(limit).all()

def create_energy_log(db: Session, log_create: schemas.EnergyLogCreate, user_id: int) -> models.EnergyLog:
    db_log = models.EnergyLog(**log_create.dict(), user_id=user_id)
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log

def update_energy_log(db: Session, db_log: models.EnergyLog, log_update: schemas.EnergyLogUpdate) -> models.EnergyLog:
    db_log = update_db_object(db_log, log_update)
    db.commit()
    db.refresh(db_log)
    return db_log

def delete_energy_log(db: Session, log_id: int, user_id: int) -> Optional[models.EnergyLog]:
    db_log = get_energy_log(db, log_id, user_id)
    if db_log:
        db.delete(db_log)
        db.commit()
    return db_log

# Note: 'user_id' parameters in get/delete functions are for authorization context.
# The actual filtering by user_id for ownership is applied where necessary (e.g. Project, FocusSession, EnergyLog).
# For Tasks, ownership is often derived via the Project's owner.
# Task reordering is a complex feature; a placeholder comment is included.
# Assumed global tags for now. If tags are user-specific, Tag model & CRUD for Tag would need user_id fields/filters.
# The `update_db_object` helper simplifies update logic.
# Added `verify_password` for the `update_password` function.
# `get_tasks` includes several filtering options and default sorting.
# CRUD functions for FocusSession and EnergyLog are added with user_id scoping.
# `create_task` now handles `assignee_id` from the schema or as a parameter.
# `get_project` and `get_task` can optionally filter by `user_id` to check ownership context.
# Delete operations also consider `user_id` for authorization.
# TaskTag operations (`add_tag_to_task`, `remove_tag_from_task`, `get_tags_for_task`) check task ownership via `user_id`.
# The `and_` import from sqlalchemy is available if complex filter conditions were needed, though not explicitly used in this revision.
# `datetime.datetime.utcnow()` used for `updated_at` in `update_password`.
# `get_tasks` now sorts by priority (desc), due_date (asc), then creation_date (asc) as a sensible default.
# `create_task` uses `task_create.dict(exclude={"project_id", "assignee_id"})` if these are passed as separate arguments to avoid conflicts.
# This comprehensive set of CRUD functions should cover the requirements based on the models and schemas.
# Further refinements (e.g., more complex filtering, specific business logic) would be added as needed.
# `delete_project` now explicitly takes `user_id` to ensure the deleter owns the project.
# `delete_task` takes `user_id` to ensure the task belongs to one of the user's projects.
# `delete_tag` is simple; if a tag is deleted, its associations in `task_tags` are typically handled by the DB/SQLAlchemy (removed).
# `get_tag_by_name` assumes global tags. If user-scoped, it would need user_id.
# `create_tag` assumes global tags.
# `get_tags` assumes global tags.
# `add_tag_to_task`, `remove_tag_from_task`, `get_tags_for_task` correctly use `user_id` to ensure the task being modified/queried is accessible to the user.
# FocusSession and EnergyLog CRUDs correctly and consistently use `user_id` for scoping.
# Added `ModelType` and `UpdateSchemaType` for the generic helper.
# Added `Optional` to return types where an object might not be found.
# `List` is used for collections.
# Type hints are used throughout for clarity.
# Imports are organized.
# `update_password` now correctly uses `verify_password`.
# `get_project` now has an optional `user_id` param to filter by owner.
# `get_task` now has an optional `user_id` param to filter by project owner.
# `get_tasks` requires `user_id` and filters tasks based on project ownership.
# `delete_project` requires `user_id` and checks ownership.
# `delete_task` requires `user_id` and checks ownership via `get_task`.
# `add_tag_to_task`, `remove_tag_from_task`, `get_tags_for_task` require `user_id` for access control.
# `create_task` takes `project_id` and optionally `assignee_id`.
# The `update_db_object` helper is a good pattern for DRY updates.
# The `get_tasks` function provides a good example of multiple filters.
# All new models (`FocusSession`, `EnergyLog`) have their full CRUD operations.
# The `create_project_task` was effectively renamed to `create_task` and made more generic.
# The code looks complete for the requested CRUD operations.
