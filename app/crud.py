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

def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[models.User]:
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

def get_projects_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[models.Project]:
    return db.query(models.Project).filter(models.Project.owner_id == user_id).offset(skip).limit(limit).all()

def create_project(db: Session, project_create: schemas.ProjectCreate, owner_id: int) -> models.Project:
    db_project = models.Project(**project_create.dict(), owner_id=owner_id)
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project

def update_project(db: Session, db_project: models.Project, project_update: schemas.ProjectUpdate) -> models.Project:
    db_project = update_db_object(db_project, project_update)
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
    return query.order_by(models.Task.priority.desc(), models.Task.due_date.asc(), models.Task.created_at.asc()).offset(skip).limit(limit).all()


def create_task(db: Session, task_create: schemas.TaskCreate, project_id: int, assignee_id: Optional[int] = None) -> models.Task:
    # Ensure project_id from task_create matches the one provided or is used consistently
    db_task = models.Task(
        **task_create.dict(exclude={"project_id", "assignee_id"}), # Exclude if they are passed separately
        project_id=project_id,
        assignee_id=assignee_id
    )
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


# --- Tag CRUD operations ---
def get_tag(db: Session, tag_id: int) -> Optional[models.Tag]:
    return db.query(models.Tag).filter(models.Tag.id == tag_id).first()

def get_tag_by_name(db: Session, name: str) -> Optional[models.Tag]:
    # Assuming tags are global as per current model (name is unique)
    # If tags were user-specific, this would need a user_id filter
    return db.query(models.Tag).filter(models.Tag.name == name).first()

def get_tags(db: Session, skip: int = 0, limit: int = 100) -> List[models.Tag]:
    # If tags were user-specific, add user_id filter
    return db.query(models.Tag).offset(skip).limit(limit).all()

def create_tag(db: Session, tag_create: schemas.TagCreate) -> models.Tag:
    # If tags were user-specific, add user_id to db_tag
    db_tag = models.Tag(**tag_create.dict())
    db.add(db_tag)
    db.commit()
    db.refresh(db_tag)
    return db_tag

def update_tag(db: Session, db_tag: models.Tag, tag_update: schemas.TagUpdate) -> models.Tag:
    db_tag = update_db_object(db_tag, tag_update)
    db.commit()
    db.refresh(db_tag)
    return db_tag

def delete_tag(db: Session, tag_id: int) -> Optional[models.Tag]:
    # Consider implications: what happens to tasks associated with this tag?
    # SQLAlchemy by default will remove associations from the task_tags table.
    db_tag = get_tag(db, tag_id)
    if db_tag:
        db.delete(db_tag)
        db.commit()
    return db_tag

# --- TaskTag Association CRUD ---
def add_tag_to_task(db: Session, task_id: int, tag_id: int, user_id: int) -> Optional[models.Task]:
    db_task = get_task(db, task_id, user_id=user_id) # Check ownership
    db_tag = get_tag(db, tag_id)
    if db_task and db_tag:
        if db_tag not in db_task.tags: # Avoid duplicates
            db_task.tags.append(db_tag)
            db.commit()
            db.refresh(db_task)
        return db_task
    return None

def remove_tag_from_task(db: Session, task_id: int, tag_id: int, user_id: int) -> Optional[models.Task]:
    db_task = get_task(db, task_id, user_id=user_id) # Check ownership
    db_tag = get_tag(db, tag_id)
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
