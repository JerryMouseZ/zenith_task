# Project management router
from fastapi import APIRouter, Depends, HTTPException, status, Response, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from .. import crud, schemas, models
from ..dependencies import get_db, get_current_active_user

router = APIRouter(
    tags=["projects"],
    dependencies=[Depends(get_current_active_user)], # All project routes require an active user
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=schemas.Project, status_code=status.HTTP_201_CREATED)
async def create_new_project(
    project: schemas.ProjectCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    """
    Create a new project for the current user.
    """
    return crud.create_project(db=db, project_create=project, owner_id=current_user.id)

@router.get("/", response_model=List[schemas.Project])
async def read_user_projects(
    archived: Optional[bool] = Query(False, description="Filter by archived status. False returns active (non-archived) projects."),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    """
    Retrieve all projects for the current user.
    - `archived=True` retrieves only archived projects.
    - `archived=False` (default) retrieves only active (non-archived) projects.
    - To get all projects (both active and archived), this parameter should be omitted by the client
      if the API/CRUD layer is designed to interpret absence of the param as "all".
      However, with `Query(False,...)`, if the client omits `archived`, it defaults to `False`.
      If "all projects" is a required use case, a different default or an explicit "all" value might be needed.
      For now, adhering to `api.md` implying default `False`.
    """
    projects = crud.get_projects_by_user(
        db,
        user_id=current_user.id,
        archived=archived, # Pass the 'archived' status to the CRUD function
        skip=skip,
        limit=limit
    )
    return projects

@router.get("/{project_id}", response_model=schemas.Project)
async def read_single_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    """
    Retrieve a specific project by its ID.
    Ensures the project belongs to the current user.
    """
    db_project = crud.get_project(db, project_id=project_id, user_id=current_user.id)
    if db_project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found or not accessible")
    return db_project

@router.put("/{project_id}", response_model=schemas.Project)
async def update_existing_project(
    project_id: int,
    project_update: schemas.ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    """
    Update an existing project.
    Ensures the project belongs to the current user before updating.
    """
    db_project = crud.get_project(db, project_id=project_id, user_id=current_user.id)
    if db_project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found or not accessible for update")

    updated_project = crud.update_project(db=db, db_project=db_project, project_update=project_update)
    return updated_project

@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    """
    Delete an existing project.
    Ensures the project belongs to the current user before deleting.
    """
    deleted_project = crud.delete_project(db, project_id=project_id, user_id=current_user.id)
    if deleted_project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found or not accessible for deletion")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
