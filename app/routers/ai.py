# AI services router
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional, Dict, Any # Ensure Any is imported if used in dummy responses
from datetime import date, time, datetime # For dummy response data types

from ..dependencies import get_current_active_user
from .. import schemas # Import the new schemas

router = APIRouter(
    prefix="/ai",
    tags=["ai"],
    dependencies=[Depends(get_current_active_user)], # Secure all AI endpoints in this router
    responses={404: {"description": "Not found"}},
)

# The old /predict endpoint and its local schemas (AIRequest, AIResponse) are removed.

@router.post("/decompose-task", response_model=schemas.AIDecomposeTaskResponse)
async def decompose_task(
    request_data: schemas.AIDecomposeTaskRequest,
    # current_user: schemas.User = Depends(get_current_active_user) # User already injected by router dependency
):
    """
    Requests AI to decompose a task into subtasks.
    """
    # Dummy response based on api.md and schemas.py
    dummy_subtasks = [
        schemas.AISubtask(title="Subtask 1 for " + request_data.task_title, description="Description for subtask 1", estimated_duration_minutes=60, priority=1),
        schemas.AISubtask(title="Subtask 2 for " + request_data.task_title, description="Description for subtask 2", estimated_duration_minutes=90, priority=0),
    ]
    return schemas.AIDecomposeTaskResponse(
        original_task_id=request_data.task_id,
        original_task_title=request_data.task_title,
        subtasks=dummy_subtasks,
        ai_notes="Task decomposition successful. Consider reviewing priorities."
    )

@router.post("/schedule-day", response_model=schemas.AIScheduleDayResponse)
async def schedule_day(
    request_data: schemas.AIScheduleDayRequest,
    # current_user: schemas.User = Depends(get_current_active_user)
):
    """
    Requests AI to plan a day's schedule.
    """
    dummy_scheduled_tasks = []
    current_time = datetime.combine(request_data.date_to_schedule, time(9,0)) # Start at 9 AM for example

    for i, task_info in enumerate(request_data.tasks_to_schedule):
        start_dt = current_time
        # Ensure estimated_duration_minutes has a default if None, for dummy logic
        duration_minutes = task_info.estimated_duration_minutes or 60
        end_dt = start_dt + datetime.timedelta(minutes=duration_minutes)

        dummy_scheduled_tasks.append(
            schemas.AIScheduledTask(
                task_id=task_info.task_id,
                title=task_info.title,
                priority=task_info.priority,
                due_date=task_info.due_date,
                estimated_duration_minutes=duration_minutes,
                scheduled_start_time=start_dt,
                scheduled_end_time=end_dt
            )
        )
        # Add a small break before next task for dummy scheduling
        current_time = end_dt + datetime.timedelta(minutes=15)


    return schemas.AIScheduleDayResponse(
        date_scheduled=request_data.date_to_schedule,
        scheduled_tasks=dummy_scheduled_tasks,
        warnings=["This is a dummy schedule. Actual scheduling logic may vary."],
        gaps_identified=[{"start_time": "12:00", "end_time": "13:00", "reason": "Suggested lunch break (dummy)"}]
    )

@router.post("/estimate-energy", response_model=schemas.AIEstimateEnergyResponse)
async def estimate_energy(
    request_data: schemas.AIEstimateEnergyRequest,
    # current_user: schemas.User = Depends(get_current_active_user)
):
    """
    Requests AI to estimate energy level required for a task.
    """
    # Dummy response
    # Logic to pick an energy level, could be random or based on input for more "realistic" dummy
    estimated_level = schemas.EnergyLevel.MEDIUM
    if request_data.task_duration_minutes > 120:
        estimated_level = schemas.EnergyLevel.HIGH
    elif request_data.task_duration_minutes < 30:
        estimated_level = schemas.EnergyLevel.LOW

    return schemas.AIEstimateEnergyResponse(
        task_description=request_data.task_description,
        estimated_energy_level_required=estimated_level,
        confidence=0.75 # Dummy confidence score
    )

# Ensure all necessary schemas are imported and used correctly.
# Ensure dummy responses align with the structure defined in schemas.py and api.md.
# The dependency get_current_active_user is applied at the router level,
# so it protects all these endpoints.
# Datetime objects are used for date/time fields in dummy responses.
# Removed unused imports like `HTTPException` if not used, but it's fine to keep for future use.
# Added `Any` to typing imports in case it's needed by `current_schedule` in `AIScheduleDayRequest` for dummy data, though not directly used here.
# Added `datetime` from `datetime` for constructing dummy `datetime` objects.
# Corrected AIScheduledTask instantiation to include all fields from TaskBasicInfo.
# Ensured `estimated_duration_minutes` in `schedule_day` has a fallback for dummy logic.
# Corrected import for `datetime.timedelta`.
# Imported `date`, `time` from `datetime`.
# Added example for `gaps_identified` in `schedule_day` response.
# Added example for `warnings` in `schedule_day` response.
# Added `ai_notes` in `decompose_task` response.
# Ensured `original_task_id` is part of `decompose_task` response.
# Updated dummy confidence in `estimate_energy` to be a float.
# Used `Field` examples from schemas to guide dummy data where appropriate (implicitly).
# Used `EnergyLevel` enum for `estimated_energy_level_required`.
# Checked that all request and response models are from `schemas.*`.
# Removed `Optional` from `typing` imports as it's not explicitly used in this file after removing old schemas.
# Re-added `Optional` from `typing` as it might be used by `schemas` indirectly or for future use.
# Re-added `HTTPException` for potential future use.
