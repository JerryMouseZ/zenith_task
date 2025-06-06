# Task management router
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from typing import List, Optional
import datetime # Added import

from .. import crud, schemas, models
from ..dependencies import get_db, get_current_active_user

router = APIRouter(
    prefix="/api/tasks", # Standard prefix
    tags=["tasks"],
    dependencies=[Depends(get_current_active_user)], # All task routes require an active user
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=schemas.Task, status_code=status.HTTP_201_CREATED)
async def create_new_task(
    task_create: schemas.TaskCreate, # schema now includes project_id, title, description, etc.
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    """
    Create a new task.
    The project specified in `task_create.project_id` must belong to the current user.
    `assignee_id` can be optionally set in `task_create`.
    """
    project = crud.get_project(db, project_id=task_create.project_id, user_id=current_user.id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, # Or 404 if project_id itself is invalid
            detail="Project not found or user does not have access to it.",
        )

    # crud.create_task expects project_id and optionally assignee_id separately from task_create fields
    # if schemas.TaskCreate includes assignee_id, it will be used.
    created_task = crud.create_task(db=db, task_create=task_create, project_id=task_create.project_id, assignee_id=getattr(task_create, 'assignee_id', None))
    return created_task

@router.get("/", response_model=List[schemas.Task])
async def read_user_tasks(
    project_id: Optional[int] = None,
    # parent_task_id: Optional[int] = None, # Assuming Task model has parent_id
    completed: Optional[bool] = None, # Renamed from 'status' for clarity with boolean field
    priority: Optional[int] = None,
    due_date_start: Optional[datetime.datetime] = None,
    due_date_end: Optional[datetime.datetime] = None,
    # is_recurring: Optional[bool] = None, # Assuming Task model has is_recurring
    # tags: Optional[List[str]] = None, # Filtering by tag names/IDs. Needs List from Query: from fastapi import Query; tags: Optional[List[str]] = Query(None)
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    """
    Retrieve tasks for the current user with extensive filtering options.
    """
    # TODO: Update crud.get_tasks to handle parent_task_id, is_recurring, tags filters.
    # For `tags` filter, `crud.get_tasks` would need to handle a list of tag names or IDs.
    tasks = crud.get_tasks(
        db,
        user_id=current_user.id,
        project_id=project_id,
        completed=completed,
        # parent_id=parent_task_id, # Pass if/when supported by CRUD
        priority=priority,
        due_date_after=due_date_start, # Parameter name mapping
        due_date_before=due_date_end,  # Parameter name mapping
        # is_recurring=is_recurring, # Pass if/when supported by CRUD
        # tags=tags, # Pass if/when supported by CRUD
        skip=skip,
        limit=limit
    )
    return tasks

@router.get("/{task_id}", response_model=schemas.Task)
async def read_single_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    """
    Retrieve a specific task by its ID.
    Ensures the task belongs to a project owned by the current user.
    """
    db_task = crud.get_task(db, task_id=task_id, user_id=current_user.id)
    if db_task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found or not accessible")
    return db_task

@router.put("/{task_id}", response_model=schemas.Task)
async def update_existing_task(
    task_id: int,
    task_update: schemas.TaskUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    """
    Update an existing task.
    Ensures the task belongs to a project owned by the current user.
    If `task_update.project_id` is provided, verifies new project belongs to user.
    """
    db_task = crud.get_task(db, task_id=task_id, user_id=current_user.id)
    if db_task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found or not accessible for update")

    if task_update.project_id and task_update.project_id != db_task.project_id:
        new_project = crud.get_project(db, project_id=task_update.project_id, user_id=current_user.id)
        if not new_project:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="New project not found or not accessible.")

    updated_task = crud.update_task(db=db, db_task=db_task, task_update=task_update)
    return updated_task

@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    """
    Delete an existing task.
    Ensures the task belongs to a project owned by the current user.
    """
    deleted_task = crud.delete_task(db, task_id=task_id, user_id=current_user.id)
    if deleted_task is None: # crud.delete_task returns the object if deleted, or None
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found or not accessible for deletion")
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.post("/{task_id}/subtasks", response_model=schemas.Task, status_code=status.HTTP_201_CREATED)
async def create_subtask_for_task(
    task_id: int, # Parent task ID
    subtask_create: schemas.TaskCreate, # Subtask details. project_id should match parent's project
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    """
    Create a subtask for a given parent task.
    The parent task must belong to the current user.
    The subtask will be associated with the same project as the parent task.
    (Assumes Task model has `parent_id` and TaskCreate schema can convey it,
     or `crud.create_task` can set it).
    """
    parent_task = crud.get_task(db, task_id=task_id, user_id=current_user.id)
    if not parent_task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parent task not found or not accessible.")

    if subtask_create.project_id != parent_task.project_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Subtask's project ID must match parent task's project ID.")

    # TODO: Modify crud.create_task to accept parent_id or modify TaskCreate schema
    # For now, assuming TaskCreate can include parent_id or crud.create_task handles it via kwargs.
    # Example: db_subtask = crud.create_task(db, task_create=subtask_create, project_id=parent_task.project_id, parent_id=task_id)
    # This requires `parent_id` to be a parameter in `crud.create_task` or part of `TaskCreate` schema that `crud.create_task` uses.
    # For this implementation, let's assume `TaskCreate` has an optional `parent_id` field.
    # And that `models.Task` also has `parent_id`.

    # Create a new TaskCreate object that includes parent_id.
    # This is a bit of a workaround if TaskCreate doesn't directly support parent_id.
    # A cleaner way is to have parent_id in TaskCreate schema.
    actual_subtask_create_data = subtask_create.dict()
    actual_subtask_create_data['parent_id'] = task_id # Assuming Task model and crud.create_task can handle this.

    # If TaskCreate schema is updated to include parent_id:
    # subtask_create_with_parent = schemas.TaskCreate(**subtask_create.dict(), parent_id=task_id)
    # created_subtask = crud.create_task(db=db, task_create=subtask_create_with_parent, project_id=parent_task.project_id)

    # This part is highly dependent on how `parent_id` is structured in models and schemas.
    # For now, raising NotImplementedError as it needs model/schema/CRUD updates.
    raise HTTPException(status_code=501, detail="Subtask creation: parent_id handling in model/schema/CRUD needs implementation.")
    # return created_subtask


@router.put("/reorder", response_model=List[schemas.Task])
async def reorder_tasks_batch(
    reorder_items: List[schemas.TaskReorderItem],
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    """
    Batch update task order or other attributes like status/project.
    (Requires a new CRUD function `crud.reorder_tasks` and Task model to have an `order` field).
    """
    # TODO: Implement crud.reorder_tasks(db, reorder_items, user_id)
    # This function would iterate through items, verify ownership of each task,
    # and update its order field (or other relevant fields).
    # It should be an atomic operation if possible or handle rollbacks.
    raise HTTPException(status_code=501, detail="Task reordering not yet implemented.")
    # updated_tasks = await crud.reorder_tasks(db, items=reorder_items, user_id=current_user.id)
    # return updated_tasks


# --- Task-Tag Association Endpoints ---
@router.post("/{task_id}/tags/{tag_id}", response_model=schemas.Task, status_code=status.HTTP_201_CREATED)
async def add_tag_to_a_task(
    task_id: int,
    tag_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    """
    Add a tag to a specific task.
    Ensures task belongs to user and tag exists.
    """
    # Verify task belongs to user (done by crud.get_task with user_id)
    # crud.add_tag_to_task will also get the task and tag
    updated_task = crud.add_tag_to_task(db=db, task_id=task_id, tag_id=tag_id, user_id=current_user.id)
    if not updated_task:
        # This could be because task or tag not found, or task not accessible by user
        # crud.add_tag_to_task should ideally raise specific exceptions or return clearer status
        task_exists = crud.get_task(db, task_id=task_id, user_id=current_user.id)
        if not task_exists:
             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found or not accessible.")
        tag_exists = crud.get_tag(db, tag_id=tag_id) # Assuming global tags, no user_id needed for get_tag
        if not tag_exists:
             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found.")
        # If both exist but linking failed for other reasons (e.g. already linked and crud handles it silently)
        # or if add_tag_to_task returns None because it couldn't find the task (already checked by task_exists)
        # For now, a generic error if updated_task is None after checks.
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to add tag to task.")
    return updated_task

@router.delete("/{task_id}/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_tag_from_a_task(
    task_id: int,
    tag_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    """
    Remove a tag from a specific task.
    Ensures task belongs to user.
    """
    updated_task = crud.remove_tag_from_task(db=db, task_id=task_id, tag_id=tag_id, user_id=current_user.id)
    if updated_task is None: # Indicates task not found, not owned, or tag not on task
        # More specific error checking can be done here similar to add_tag_to_task
        task_check = crud.get_task(db, task_id, user_id=current_user.id)
        if not task_check:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found or not accessible.")
        # If task exists but operation failed, could be tag not on task or tag itself not found
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to remove tag, tag may not be associated or task/tag not found.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.get("/{task_id}/tags", response_model=List[schemas.Tag])
async def get_all_tags_for_a_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    """
    Get all tags associated with a specific task.
    Ensures task belongs to user.
    """
    # crud.get_tags_for_task already checks task ownership if user_id is passed
    tags = crud.get_tags_for_task(db=db, task_id=task_id, user_id=current_user.id)
    # The crud.get_tags_for_task returns empty list if task not found or no tags,
    # so we might need an explicit check if task itself exists and is accessible if API requires 404 for task.
    if not crud.get_task(db, task_id=task_id, user_id=current_user.id) and not tags:
         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found or not accessible.")
    return tags

# General Notes:
# - Standardized prefix to /api/tasks.
# - All routes are async and depend on get_current_active_user.
# - create_new_task: uses crud.create_task, ensures project ownership, returns 201.
# - read_user_tasks: Implemented with various filter parameters. Noted TODOs for filters not yet fully supported by current CRUD/models (parent_task_id, is_recurring, tags).
# - read_single_task: Uses crud.get_task with user_id scoping.
# - update_existing_task: Fetches task with user_id scoping, then updates. Verifies new project ownership if project_id is changed.
# - delete_existing_task: Uses crud.delete_task with user_id scoping, returns 204.
# - create_subtask_for_task: Endpoint structure created. Marked as 501 Not Implemented due to model/schema/CRUD dependencies for parent_id.
# - reorder_tasks_batch: Endpoint structure created. Marked as 501 Not Implemented due to complex CRUD dependency.
# - Task-Tag routes:
#   - POST /{task_id}/tags/{tag_id}: Uses crud.add_tag_to_task, returns updated task (or 201). Added more detailed error checking.
#   - DELETE /{task_id}/tags/{tag_id}: Uses crud.remove_tag_from_task, returns 204. Added more detailed error checking.
#   - GET /{task_id}/tags: Uses crud.get_tags_for_task. Added check for task existence for 404.
# - Imported datetime, Response, status.
# - `completed` is used for task status filter, mapping to the boolean field.
# - `due_date_start` and `due_date_end` map to `due_date_after` and `due_date_before` in CRUD.
# - The `assignee_id` in `create_new_task` uses `getattr` as a safe way to access it from `task_create` if it's optional.
# - The `create_subtask_for_task` has a placeholder for how `parent_id` might be handled.
# - Error handling for task/tag association routes made more specific.
# - `create_new_task` now checks project ownership correctly.
# - `update_existing_task` now correctly passes `db_task` object to `crud.update_task`.
# - `delete_existing_task` uses `crud.delete_task` which returns the deleted object or None.
# - `add_tag_to_a_task` status code set to 201.
# - `remove_tag_from_a_task` status code set to 204.
# - `get_all_tags_for_a_task` returns List[schemas.Tag].
# - The complex filters in `read_user_tasks` are passed to `crud.get_tasks`.
#   The commented out ones (parent_task_id, is_recurring, tags) indicate features that need model/CRUD updates.
# - The subtask creation and reorder endpoints are correctly marked as needing further backend work (501).
# - The current `crud.create_task` signature is `(db, task_create, project_id, assignee_id)`. This is used.
# - The current `crud.update_task` signature is `(db, db_task, task_update)`. This is used.
# - The current `crud.delete_task` signature is `(db, task_id, user_id)`. This is used.
# - The current `crud.add_tag_to_task` signature is `(db, task_id, tag_id, user_id)`. This is used.
# - The current `crud.remove_tag_from_task` signature is `(db, task_id, tag_id, user_id)`. This is used.
# - The current `crud.get_tags_for_task` signature is `(db, task_id, user_id)`. This is used.
# All CRUD calls align with the previously defined signatures.
# The logic for verifying project ownership before task creation is sound.
# The logic for verifying task ownership (via project) for get/update/delete is sound.
# The task-tag association endpoints also correctly verify task ownership.
# Tag ownership is not currently checked as tags are global, this is consistent.
# Looks good.
