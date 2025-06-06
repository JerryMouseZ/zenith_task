from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from typing import List, Optional, Any
import datetime

from .. import crud, models, schemas
from ..dependencies import get_current_active_user, get_db

# Main router for all /api/monitoring endpoints
monitoring_router = APIRouter(
    prefix="/api/monitoring",
    tags=["monitoring"],
    dependencies=[Depends(get_current_active_user)],
    responses={404: {"description": "Not found"}},
)

# --- Focus Sessions Router ---
focus_sessions_router = APIRouter(
    prefix="/focus-sessions",
    tags=["focus-sessions"],
)

@focus_sessions_router.post("/", response_model=schemas.FocusSession, status_code=status.HTTP_201_CREATED)
def create_focus_session_endpoint( # Renamed to avoid conflict with schema name
    focus_session_create: schemas.FocusSessionCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    # Logic to handle duration/end_time consistency if needed
    # For example, if start_time and end_time are provided, calculate duration_minutes
    temp_focus_session_data = focus_session_create.dict()
    if temp_focus_session_data.get("start_time") and temp_focus_session_data.get("end_time") and temp_focus_session_data.get("duration_minutes") is None:
        duration_delta = temp_focus_session_data["end_time"] - temp_focus_session_data["start_time"]
        if duration_delta.total_seconds() < 0:
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="end_time cannot be before start_time")
        temp_focus_session_data["duration_minutes"] = int(duration_delta.total_seconds() / 60)
    elif temp_focus_session_data.get("start_time") and temp_focus_session_data.get("duration_minutes") is not None and temp_focus_session_data.get("end_time") is None:
        temp_focus_session_data["end_time"] = temp_focus_session_data["start_time"] + datetime.timedelta(minutes=temp_focus_session_data["duration_minutes"])

    # Re-create the schema with potentially updated fields to pass to CRUD
    # This ensures that the status field with its default value from FocusSessionBase is included.
    # And any calculated fields (end_time/duration_minutes) are part of the object.
    final_session_data = schemas.FocusSessionCreate(**temp_focus_session_data)

    return crud.create_focus_session(db=db, focus_session=final_session_data, user_id=current_user.id)

@focus_sessions_router.get("/", response_model=List[schemas.FocusSession])
def read_focus_sessions_endpoint( # Renamed
    task_id: Optional[int] = None,
    date_start: Optional[datetime.datetime] = None,
    date_end: Optional[datetime.datetime] = None,
    status_filter: Optional[schemas.FocusSessionStatus] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    return crud.get_focus_sessions(
        db=db, user_id=current_user.id, task_id=task_id,
        start_time_after=date_start, start_time_before=date_end,
        status=status_filter, skip=skip, limit=limit
    )

@focus_sessions_router.get("/{session_id}", response_model=schemas.FocusSession)
def read_focus_session_endpoint( # Renamed
    session_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    db_focus_session = crud.get_focus_session(db=db, session_id=session_id, user_id=current_user.id)
    if db_focus_session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Focus session not found")
    return db_focus_session

@focus_sessions_router.put("/{session_id}", response_model=schemas.FocusSession)
def update_focus_session_endpoint( # Renamed
    session_id: int,
    focus_session_update: schemas.FocusSessionUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    db_focus_session = crud.get_focus_session(db=db, session_id=session_id, user_id=current_user.id)
    if db_focus_session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Focus session not found")

    update_data = focus_session_update.dict(exclude_unset=True)

    # Recalculate duration or end_time if relevant fields are updated
    # Get current values from db_focus_session and override with any from update_data
    current_start = update_data.get('start_time', db_focus_session.start_time)
    current_end = update_data.get('end_time', db_focus_session.end_time)
    current_duration = update_data.get('duration_minutes', db_focus_session.duration_minutes)
    current_status = update_data.get('status', db_focus_session.status)

    # Create a new FocusSessionUpdate instance to pass to CRUD to avoid modifying input
    processed_update_data = update_data.copy()

    if 'duration_minutes' in update_data and update_data['duration_minutes'] is not None:
        if current_start:
            processed_update_data['end_time'] = current_start + datetime.timedelta(minutes=update_data['duration_minutes'])
    elif ('start_time' in update_data or 'end_time' in update_data):
        # This case handles if start_time or end_time is changed, then duration should be recalculated
        # but only if duration_minutes was NOT part of the update request.
        # If end_time is explicitly set to None (e.g. session restarted), duration might become None too.
        if current_start and current_end:
            if current_end < current_start:
                 raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="end_time cannot be before start_time")
            delta = current_end - current_start
            processed_update_data['duration_minutes'] = int(delta.total_seconds() / 60)
        else: # If either start or end becomes None (and duration wasn't set), duration becomes None
            processed_update_data['duration_minutes'] = None

    # If session is completed, ensure end_time is set
    if processed_update_data.get('status') == schemas.FocusSessionStatus.COMPLETED and not current_end:
        processed_update_data['end_time'] = datetime.datetime.utcnow()
        # Recalculate duration if end_time was just set
        if current_start and processed_update_data.get('end_time'):
            delta = processed_update_data['end_time'] - current_start
            processed_update_data['duration_minutes'] = int(delta.total_seconds() / 60)


    final_update_schema = schemas.FocusSessionUpdate(**processed_update_data)
    return crud.update_focus_session(db=db, db_focus_session=db_focus_session, focus_session_update=final_update_schema)

@focus_sessions_router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_focus_session_endpoint( # Renamed
    session_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    db_focus_session = crud.delete_focus_session(db=db, session_id=session_id, user_id=current_user.id)
    if db_focus_session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Focus session not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# --- Energy Logs Router ---
energy_logs_router = APIRouter(
    prefix="/energy-logs",
    tags=["energy-logs"],
)

@energy_logs_router.post("/", response_model=schemas.EnergyLog, status_code=status.HTTP_201_CREATED)
def create_energy_log_endpoint( # Renamed
    energy_log: schemas.EnergyLogCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    return crud.create_energy_log(db=db, energy_log=energy_log, user_id=current_user.id)

@energy_logs_router.get("/", response_model=List[schemas.EnergyLog])
def read_energy_logs_endpoint( # Renamed
    date_start: Optional[datetime.datetime] = None,
    date_end: Optional[datetime.datetime] = None,
    energy_level: Optional[schemas.EnergyLevel] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    if date_end is not None and date_end.time() == datetime.time.min:
        date_end = datetime.datetime.combine(date_end.date(), datetime.time.max)

    return crud.get_energy_logs(
        db=db, user_id=current_user.id,
        timestamp_after=date_start, timestamp_before=date_end,
        energy_level=energy_level, skip=skip, limit=limit
    )

@energy_logs_router.get("/{log_id}", response_model=schemas.EnergyLog)
def read_energy_log_endpoint( # Renamed
    log_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    db_energy_log = crud.get_energy_log(db=db, log_id=log_id, user_id=current_user.id)
    if db_energy_log is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Energy log not found")
    return db_energy_log

@energy_logs_router.put("/{log_id}", response_model=schemas.EnergyLog)
def update_energy_log_endpoint( # Renamed
    log_id: int,
    energy_log_update: schemas.EnergyLogUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    db_energy_log = crud.get_energy_log(db=db, log_id=log_id, user_id=current_user.id)
    if db_energy_log is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Energy log not found")
    return crud.update_energy_log(db=db, db_energy_log=db_energy_log, energy_log_update=energy_log_update)

@energy_logs_router.delete("/{log_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_energy_log_endpoint( # Renamed
    log_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    db_energy_log = crud.delete_energy_log(db=db, log_id=log_id, user_id=current_user.id)
    if db_energy_log is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Energy log not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# --- Reports Router ---
reports_router = APIRouter(
    prefix="/reports",
    tags=["reports"],
)

@reports_router.get("/energy", response_model=schemas.EnergyReport)
def get_energy_report_endpoint( # Renamed
    period: str = "daily",
    date_start: datetime.date = datetime.date.today() - datetime.timedelta(days=7),
    date_end: datetime.date = datetime.date.today(),
    current_user: models.User = Depends(get_current_active_user),
):
    dummy_data_points = [
        schemas.EnergyReportDataPoint(timestamp=datetime.datetime.combine(date_start + datetime.timedelta(days=i), datetime.time(10,0)), energy_level=schemas.EnergyLevel.MEDIUM if i % 2 == 0 else schemas.EnergyLevel.HIGH)
        for i in range((date_end - date_start).days + 1)
    ]
    if not dummy_data_points and (date_end - date_start).days >=0 : # Ensure at least one point if period is valid
         dummy_data_points.append(schemas.EnergyReportDataPoint(timestamp=datetime.datetime.combine(date_start, datetime.time(10,0)), energy_level=schemas.EnergyLevel.MEDIUM))


    return schemas.EnergyReport(
        user_id=current_user.id,
        report_period_start=date_start,
        report_period_end=date_end,
        average_energy_level=3.5 if dummy_data_points else None,
        energy_trend="stable" if dummy_data_points else "no_data",
        data_points=dummy_data_points
    )

@reports_router.get("/task-completion", response_model=schemas.TaskCompletionReport)
def get_task_completion_report_endpoint( # Renamed
    period: str = "weekly",
    date_start: datetime.date = datetime.date.today() - datetime.timedelta(days=7),
    date_end: datetime.date = datetime.date.today(),
    project_id: Optional[int] = None,
    current_user: models.User = Depends(get_current_active_user),
):
    start_dt = datetime.datetime.combine(date_start, datetime.time.min)
    end_dt = datetime.datetime.combine(date_end, datetime.time.max)

    dummy_details = [
        schemas.TaskCompletionReportEntry(project_name=f"Project Alpha {project_id if project_id else ''}", task_title="Design Homepage", completed_at=start_dt + datetime.timedelta(days=2), due_date=start_dt + datetime.timedelta(days=3), status="completed_on_time"),
        schemas.TaskCompletionReportEntry(project_name="Project Beta", task_title="Develop API", completed_at=None, due_date=end_dt - datetime.timedelta(days=1), status="pending"),
    ]
    return schemas.TaskCompletionReport(
        user_id=current_user.id,
        report_period_start=date_start,
        report_period_end=date_end,
        total_tasks=2,
        tasks_completed=1,
        completion_rate=0.5,
        details=dummy_details
    )

@reports_router.get("/screen-time", response_model=schemas.ScreenTimeReport)
def get_screen_time_report_endpoint( # Renamed
    period: str = "daily", # Not used in dummy logic directly, but available
    date_start: datetime.date = datetime.date.today() - datetime.timedelta(days=1),
    date_end: datetime.date = datetime.date.today(), # Using this as the report_date for dummy
    current_user: models.User = Depends(get_current_active_user),
):
    return schemas.ScreenTimeReport(
        user_id=current_user.id,
        report_date=date_end,
        productive_app_time_minutes=180,
        unproductive_app_time_minutes=60,
        neutral_app_time_minutes=30
    )

monitoring_router.include_router(focus_sessions_router)
monitoring_router.include_router(energy_logs_router)
monitoring_router.include_router(reports_router)
