# Tag management router
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError # For handling unique constraint violations
from typing import List

from .. import crud, schemas, models
from ..dependencies import get_db, get_current_active_user

router = APIRouter(
    prefix="/api/tags",
    tags=["tags"],
    dependencies=[Depends(get_current_active_user)],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=schemas.Tag, status_code=status.HTTP_201_CREATED)
async def create_new_tag(
    tag_create: schemas.TagCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    """
    Create a new tag for the current user.
    Tag names must be unique per user.
    """
    try:
        created_tag = crud.create_tag(db=db, tag_create=tag_create, user_id=current_user.id)
        return created_tag
    except ValueError as e: # Catch custom ValueError for name collision from CRUD
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except IntegrityError: # Catch DB level unique constraint violation if CRUD didn't catch it first
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, # 409 Conflict is more appropriate for duplicates
            detail="Tag name already exists for this user.",
        )


@router.get("/", response_model=List[schemas.Tag])
async def read_user_tags(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    """
    Retrieve all tags for the current user.
    """
    tags = crud.get_tags_by_user(db=db, user_id=current_user.id, skip=skip, limit=limit)
    return tags

@router.get("/{tag_id}", response_model=schemas.Tag)
async def read_single_tag(
    tag_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    """
    Retrieve a specific tag by its ID, owned by the current user.
    """
    db_tag = crud.get_tag(db=db, tag_id=tag_id, user_id=current_user.id)
    if db_tag is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found")
    return db_tag

@router.put("/{tag_id}", response_model=schemas.Tag)
async def update_existing_tag(
    tag_id: int,
    tag_update: schemas.TagUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    """
    Update an existing tag owned by the current user.
    If name changes, uniqueness per user must be maintained.
    """
    db_tag = crud.get_tag(db=db, tag_id=tag_id, user_id=current_user.id)
    if db_tag is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found")

    try:
        updated_tag = crud.update_tag(db=db, db_tag=db_tag, tag_update=tag_update, user_id=current_user.id)
        return updated_tag
    except ValueError as e: # Catch custom ValueError for name collision from CRUD
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except IntegrityError: # Catch DB level unique constraint violation
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Tag name already exists for this user or other integrity error.",
        )

@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_tag(
    tag_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    """
    Delete an existing tag owned by the current user.
    """
    deleted_tag = crud.delete_tag(db=db, tag_id=tag_id, user_id=current_user.id)
    if deleted_tag is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
