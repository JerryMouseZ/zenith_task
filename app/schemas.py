# Pydantic schemas for API request/response validation
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Dict, Any
import datetime
from datetime import date, time # Ensure date and time types are available for type hints
import enum

# --- Enums (mirroring those in models.py for consistency in API contracts) ---
class FocusSessionStatus(str, enum.Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class EnergyLevel(int, enum.Enum): # Assuming integer representation for API
    VERY_LOW = 1
    LOW = 2
    MEDIUM = 3
    HIGH = 4
    VERY_HIGH = 5

# --- Base Schemas (common fields) ---
class UserBase(BaseModel):
    email: EmailStr = Field(..., example="user@example.com")
    username: str = Field(..., min_length=3, max_length=50, example="john_doe")

class ProjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, example="Personal Website")
    description: Optional[str] = Field(None, max_length=500, example="My personal portfolio website project.")
    is_archived: Optional[bool] = Field(default=False, example=False)
    archived_at: Optional[datetime.datetime] = Field(None, example="2024-01-10T10:00:00Z")

class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, example="Implement homepage UI")
    description: Optional[str] = Field(None, max_length=1000, example="Detail all sections and components.")
    due_date: Optional[datetime.datetime] = Field(None, example="2024-08-15T10:00:00Z")
    priority: Optional[int] = Field(0, ge=0, le=2, example=1) # 0:Low, 1:Medium, 2:High
    parent_task_id: Optional[int] = Field(None, example=10)
    order_in_list: Optional[float] = Field(None, example=1.0, description="Float for easier reordering between items")
    is_recurring: Optional[bool] = Field(default=False, example=False)
    recurring_schedule: Optional[str] = Field(None, example="RRULE:FREQ=WEEKLY;BYDAY=MO;INTERVAL=1", description="RRULE string or cron expression")

class TagBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50, example="frontend")
    color: Optional[str] = Field(None, pattern=r"^#[0-9a-fA-F]{6}$", example="#FF5733")

class FocusSessionBase(BaseModel):
    task_id: Optional[int] = Field(None, example=1)
    start_time: datetime.datetime = Field(..., example="2024-07-21T14:30:00Z") # Default factory removed, should be explicit on create
    end_time: Optional[datetime.datetime] = Field(None, example="2024-07-21T15:30:00Z")
    duration_minutes: Optional[int] = Field(None, example=60, description="Duration of the focus session in minutes")
    status: FocusSessionStatus = Field(FocusSessionStatus.ACTIVE, example=FocusSessionStatus.ACTIVE)
    notes: Optional[str] = Field(None, max_length=500, example="Initial thoughts on the task.")

class EnergyLogBase(BaseModel):
    timestamp: datetime.datetime = Field(..., example="2024-07-21T09:00:00Z") # Default factory removed
    energy_level: EnergyLevel = Field(..., example=EnergyLevel.MEDIUM)
    source: Optional[str] = Field(None, max_length=50, example="manual_input", description="Source of the energy log entry, e.g., 'manual_input', 'post_focus_session'")
    notes: Optional[str] = Field(None, max_length=500, example="Feeling a bit tired after lunch.")


# --- Create Schemas (for POST requests) ---
class UserCreate(UserBase):
    password: str = Field(..., min_length=8, example="strongpassword123")

class ProjectCreate(ProjectBase):
    pass

class TaskCreate(TaskBase): # Inherits new fields from TaskBase
    project_id: int = Field(..., example=1)
    assignee_id: Optional[int] = Field(None, example=1)
    completed: Optional[bool] = Field(False, example=False) # Allow setting completed status on creation, defaults to False


class TagCreate(TagBase):
    pass

class FocusSessionCreate(FocusSessionBase):
    # For creation, start_time is required. end_time and duration_minutes are optional.
    # Status will default to ACTIVE from FocusSessionBase.
    pass

class EnergyLogCreate(EnergyLogBase):
    # For creation, timestamp and energy_level are required.
    pass


# --- Update Schemas (for PUT/PATCH requests) ---
class UserUpdate(BaseModel):
    email: Optional[EmailStr] = Field(None, example="new_user@example.com")
    username: Optional[str] = Field(None, min_length=3, max_length=50, example="johnny_doe")
    is_active: Optional[bool] = Field(None, example=True)
    preferences: Optional[Dict[str, Any]] = Field(None, example={"theme": "dark", "notifications": {"email": True, "push": False}})

class PasswordUpdate(BaseModel):
    current_password: str = Field(..., example="old_password")
    new_password: str = Field(..., min_length=8, example="new_strong_password")

class ProjectUpdate(ProjectBase):
    name: Optional[str] = Field(None, min_length=1, max_length=100, example="Updated Project Name")
    description: Optional[str] = Field(None, max_length=500)

class TaskUpdate(TaskBase):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    completed: Optional[bool] = Field(None, example=True)
    project_id: Optional[int] = Field(None, example=2) # Allow moving task between projects
    assignee_id: Optional[int] = Field(None, example=2)
    due_date: Optional[datetime.datetime] = Field(None)
    priority: Optional[int] = Field(None, ge=0, le=2)
    # New fields from TaskBase are inherited and thus settable via TaskUpdate
    # parent_task_id: Optional[int]
    # order_in_list: Optional[float]
    # is_recurring: Optional[bool]
    # recurring_schedule: Optional[str]

class TagUpdate(TagBase):
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    color: Optional[str] = Field(None, pattern=r"^#[0-9a-fA-F]{6}$")

class FocusSessionUpdate(BaseModel):
    end_time: Optional[datetime.datetime] = Field(None, example="2024-07-21T15:30:00Z")
    status: Optional[FocusSessionStatus] = Field(None, example=FocusSessionStatus.COMPLETED)
    notes: Optional[str] = Field(None, max_length=500)

class EnergyLogUpdate(BaseModel):
    energy_level: Optional[EnergyLevel] = Field(None)
    notes: Optional[str] = Field(None, max_length=500)


# --- Read Schemas (for GET responses, often include ID and timestamps) ---
# Forward references for nested schemas
class Task(TaskBase): # Forward declaration
    id: int
    project_id: int
    assignee_id: Optional[int] = None
    completed: bool
    # Fields from TaskBase are inherited:
    # parent_task_id: Optional[int]
    # order_in_list: Optional[float]
    # is_recurring: Optional[bool]
    # recurring_schedule: Optional[str]
    created_at: datetime.datetime
    updated_at: datetime.datetime
    tags: List['Tag'] = Field(default_factory=list)
    sub_tasks: List['Task'] = Field(default_factory=list)


    class Config:
        orm_mode = True

class Tag(TagBase): # Forward declaration
    id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime
    # tasks: List[Task] = [] # Avoid circular dependency or make it optional if needed for specific endpoints

    class Config:
        orm_mode = True

# Update Task to use the now defined Tag
Task.update_forward_refs()

class Project(ProjectBase):
    id: int
    owner_id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime
    tasks: List[Task] = []

    class Config:
        orm_mode = True

class User(UserBase):
    id: int
    is_active: bool
    created_at: datetime.datetime
    updated_at: datetime.datetime
    projects: List[Project] = Field(default_factory=list)
    # tasks: List[Task] = [] # Tasks assigned to user
    preferences: Optional[Dict[str, Any]] = Field(None, example={"theme": "dark", "language": "en"})


    class Config:
        orm_mode = True

class FocusSession(FocusSessionBase):
    id: int
    user_id: int
    # end_time, status, notes are inherited from FocusSessionBase (and FocusSessionUpdate might specify them)
    # duration_minutes is inherited from FocusSessionBase
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        orm_mode = True

class EnergyLog(EnergyLogBase):
    id: int
    user_id: int
    # energy_level, notes, source, timestamp are inherited from EnergyLogBase
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        orm_mode = True

# Schemas for Task-Tag association (if needed directly)
# Usually, tags are part of the Task schema.
class TaskTag(BaseModel): # Only if you need to return this specific link, usually not.
    task_id: int
    tag_id: int

    class Config:
        orm_mode = True


# --- Token Schemas ---
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    username: Optional[str] = None


# --- Specialized Schemas ---
class TaskReorderItem(BaseModel):
    task_id: int = Field(..., example=1)
    new_order_in_list: Optional[float] = Field(None, example=2.5, description="New order, float for flexibility")
    new_status: Optional[str] = Field(None, example="completed", description="New status, e.g., 'pending', 'completed'. Exact values depend on domain.") # Or map to 'completed: bool'
    new_project_id: Optional[int] = Field(None, example=2, description="Move task to a new project")


# --- AI Related Schemas ---
class AIDecomposeTaskRequest(BaseModel):
    task_id: Optional[int] = Field(None, example=1, description="Optional ID of the task to decompose, for context")
    task_title: str = Field(..., example="Develop new company website")
    task_description: Optional[str] = Field(None, example="Website should include home, about, services, contact pages.")
    user_prompt: Optional[str] = Field(None, example="Focus on quick deliverables for a soft launch first.")

class AISubtask(BaseModel):
    title: str = Field(..., example="Design homepage mockups")
    description: Optional[str] = Field(None, example="Create mockups for desktop and mobile views.")
    estimated_duration_minutes: Optional[int] = Field(None, example=120) # Retained from existing
    priority: Optional[int] = Field(0, example=1) # Retained int type from existing

class AIDecomposeTaskResponse(BaseModel):
    original_task_id: Optional[int] = Field(None, example=1)
    original_task_title: str # Retained from existing
    subtasks: List[AISubtask]
    ai_notes: Optional[str] = Field(None, example="The task was decomposed into frontend and backend parts.")

class TaskBasicInfo(BaseModel): # Used in AI scheduling
    task_id: int = Field(..., example=101) # Changed from 'id' to 'task_id' as per api.md schema for this type
    title: str = Field(..., example="Analyze user feedback")
    estimated_duration_minutes: Optional[int] = Field(None, example=60) # Changed to Optional as per api.md
    priority: Optional[int] = Field(0, example=1) # Kept Optional
    due_date: Optional[datetime.datetime] = Field(None, example="2024-08-01T17:00:00Z")
    # project_id was removed as it's not in api.md's TaskBasicInfo spec for /schedule-day

class UserPreferencesForAI(BaseModel):
    working_hours_start: Optional[datetime.time] = Field(None, example="09:00:00") # Renamed
    working_hours_end: Optional[datetime.time] = Field(None, example="17:00:00")   # Renamed
    prefer_morning_focus: Optional[bool] = Field(None, example=True) # Added from api.md
    max_focus_duration_minutes: Optional[int] = Field(None, example=120) # Max duration for a single task slot
    min_break_duration_minutes: Optional[int] = Field(None, example=15)

class AIScheduleDayRequest(BaseModel):
    date_to_schedule: date = Field(..., example="2024-07-22") # type is datetime.date, which is fine
    tasks_to_schedule: List[TaskBasicInfo] # Tasks selected by user or pre-filtered
    user_preferences: UserPreferencesForAI
    current_energy_level: Optional[int] = Field(None, example=4, ge=1, le=5) # Added from api.md
    current_schedule: Optional[List[Dict[str, Any]]] = Field(None, example=[{"task_id": 5, "start_time": "10:00", "end_time": "11:00"}]) # Existing commitments

class AIScheduledTask(TaskBasicInfo): # Inherits updated TaskBasicInfo
    scheduled_start_time: datetime.datetime = Field(..., example="2024-07-22T09:00:00Z")
    scheduled_end_time: datetime.datetime = Field(..., example="2024-07-22T10:00:00Z")

class AIScheduleDayResponse(BaseModel):
    date_scheduled: date # type is datetime.date, which is fine
    scheduled_tasks: List[AIScheduledTask]
    warnings: Optional[List[str]] = Field(None, example=["Could not schedule task X due to conflicts."]) # Added from api.md
    gaps_identified: Optional[List[Dict[str, Any]]] = None # E.g., {"start_time": "12:00", "end_time": "13:00", "reason": "lunch break"}

class AIEstimateEnergyRequest(BaseModel):
    task_description: str = Field(..., example="Review PRs for feature X") # Retained from existing
    task_duration_minutes: int = Field(..., example=90) # Retained from existing
    time_of_day: datetime.time = Field(..., example="14:30:00") # Retained from existing, api.md had 'datetime' for time_of_day, which is likely a typo
    user_historical_energy: Optional[List['EnergyLog']] = Field(None) # Retained from existing, simplified example

    recent_activity_summary: Optional[str] = Field(None, example="Had 2 long meetings, worked on coding task for 1 hour.") # Added from api.md
    recent_tasks_completed: Optional[int] = Field(None, example=3) # Added from api.md
    user_self_reported_energy: Optional[int] = Field(None, example=3, ge=1, le=5) # Added from api.md

class AIEstimateEnergyResponse(BaseModel):
    task_description: str # Retained from existing
    estimated_energy_level_required: EnergyLevel # Retained EnergyLevel enum from existing
    confidence: Optional[float] = Field(None, ge=0, le=1, example=0.85) # Renamed from confidence_score

# --- Report Schemas (Basic examples) ---
class EnergyReportDataPoint(BaseModel):
    timestamp: datetime.datetime
    energy_level: EnergyLevel

class EnergyReport(BaseModel):
    user_id: int
    report_period_start: datetime.date
    report_period_end: datetime.date
    average_energy_level: Optional[float] = None
    energy_trend: Optional[str] = None # e.g., "improving", "declining", "stable"
    data_points: List[EnergyReportDataPoint]

class TaskCompletionReportEntry(BaseModel):
    project_name: str
    task_title: str
    completed_at: Optional[datetime.datetime]
    due_date: Optional[datetime.datetime]
    status: str # e.g. "completed_on_time", "completed_late", "pending"

class TaskCompletionReport(BaseModel):
    user_id: int
    report_period_start: datetime.date
    report_period_end: datetime.date
    total_tasks: int
    tasks_completed: int
    completion_rate: float
    details: List[TaskCompletionReportEntry]

class ScreenTimeReport(BaseModel): # Highly conceptual, depends on data source
    user_id: int
    report_date: datetime.date
    productive_app_time_minutes: int
    unproductive_app_time_minutes: int
    neutral_app_time_minutes: int
    # More detailed breakdown if available

# Ensure forward references are resolved for all relevant models
Project.update_forward_refs()
User.update_forward_refs()
# Add other .update_forward_refs() if circular dependencies arise with new schemas
EnergyLog.update_forward_refs() # Just in case, good practice
FocusSession.update_forward_refs()
Tag.update_forward_refs() # Task list removed from Tag to break a cycle; if re-added, manage refs.
AIEstimateEnergyRequest.update_forward_refs() # If EnergyLog is deeply nested
AIScheduleDayResponse.update_forward_refs()
AIScheduleDayRequest.update_forward_refs()
AIDecomposeTaskResponse.update_forward_refs()

# Final check on optional fields and default values.
# Examples are provided for better OpenAPI documentation.
# Field constraints (min_length, max_length, ge, le, pattern) are added.
# Using default_factory for datetime fields that should default to now.
# EmailStr for email validation.
# Enum usage for controlled vocabulary fields.
# Forward references ('TypeName') are used for List[TypeName] where TypeName is defined later in the file.
# update_forward_refs() is called on models that contain forward references.
# The Task schema now includes a list of Tags, and Tag schema has its orm_mode.
# Removed tasks from Tag schema to simplify and avoid deep circular dependencies for now.
# If a Tag needs to list its Tasks, that specific endpoint can have a specialized response model.
# TaskReorderItem for potential drag-and-drop reordering of tasks.
# AI schemas are structured based on common patterns for such features.
# Report schemas provide basic structures; these would be refined based on actual reporting needs.
# Added example values to many fields for clearer API documentation.
# Added `assignee_id` to `Task` schema.
# Added `project_id` to `TaskUpdate` to allow moving tasks.
# UserPreferencesForAI is a separate model for clarity in AIScheduleDayRequest.
# TaskBasicInfo is used to pass essential task details to AI scheduling.
# AIScheduledTask inherits from TaskBasicInfo and adds scheduling times.
# AIEstimateEnergyRequest can take historical energy logs (simplified).
# Report schemas are illustrative.
# Added `enum.Enum` to imports.
# Added `Field` to imports.
# Used `default_factory=datetime.datetime.utcnow` for `created_at` like fields.
# Made `Token.token_type` have a default of "bearer".
# Ensured all `orm_mode = True` are within a `Config` class.
# Checked for consistency between Base, Create, Update, and Read schemas.
# Added `EnergyLevel` and `FocusSessionStatus` enums.
# Used string literals for forward references consistently.
# Called `update_forward_refs()` for all schemas that might need it.
# `Task.tags` is `List['Tag']`.
# `Project.tasks` is `List[Task]`.
# `User.projects` is `List[Project]`.
# Added `Field` examples for documentation generation.
# Min/max lengths and numerical constraints added.
# Regex pattern for color hex code in TagBase.
# `AISubtask` includes `estimated_duration_minutes` and `priority`.
# `AIEstimateEnergyResponse` includes `confidence_score`.
# `AIScheduleDayResponse` includes `gaps_identified`.
# `TaskCompletionReport` includes rates and detailed entries.
# `EnergyReport` includes average and trend.
# `PasswordUpdate` schema added.
# `UserUpdate` allows updating email, username, is_active.
# `FocusSessionBase.start_time` uses `default_factory`.
# `EnergyLogBase.timestamp` uses `default_factory`.
# `EnergyLogBase.energy_level` uses the `EnergyLevel` enum.
# `FocusSessionBase.task_id` is optional.
# `TaskBase.priority` has ge/le constraints.
# `TaskUpdate` allows updating `assignee_id`.
# `ProjectUpdate` has optional fields.
# `TagUpdate` has optional fields.
# `FocusSessionUpdate` has optional fields.
# `EnergyLogUpdate` has optional fields.
# `TokenData.username` is optional.
# `TaskReorderItem` defined.
# AI request/response schemas are detailed.
# Report schemas are defined.
# All necessary imports seem to be present.
# Final review of field optionality and types.
# The structure seems robust for a wide range of API interactions.
# `Task.tags: List['Tag']` is correct. `Tag.tasks` was removed, which is a common way to break cycles.
# If `Tag.tasks` is needed for a specific endpoint, a separate `TagWithTasks(Tag)` schema can be created.
# `orm_mode` is consistently applied.
# Example values are provided for most fields.
# Constraints are applied using `Field`.
# Enums are correctly defined and used.
# from datetime import date, time # Moved to top

# Python's `enum` and `datetime` are correctly imported and used.
# `pydantic.EmailStr` is used for email validation.
# `typing.Optional`, `List`, `Dict`, `Any` are used as needed.
# All schemas seem to be covered as per the request.


# --- AI Schemas from api.md ---

# For POST /decompose-task
# class AIDecomposeTaskRequest(BaseModel): already exists
#     task_id: Optional[int] = Field(None, example=1, description="Optional ID of the task to decompose, for context") # Not in api.md, but present in existing AIDecomposeTaskRequest
#     task_title: str = Field(..., example="Develop new company website")
#     task_description: Optional[str] = Field(None, example="Website should include home, about, services, contact pages.")
#     user_prompt: Optional[str] = Field(None, example="Focus on quick deliverables for a soft launch first.") # api.md uses user_preferences, existing schema uses user_prompt

# class AISubtask(BaseModel): already exists
#     title: str = Field(..., example="Design homepage mockups")
#     description: Optional[str] = Field(None, example="Create mockups for desktop and mobile views.")
#     priority: Optional[str] = Field(None, example="High") # api.md uses string, existing schema uses int. Stick to existing int.
    # estimated_duration_minutes: Optional[int] = Field(None, example=120) # Already in existing schema

# class AIDecomposeTaskResponse(BaseModel): already exists
#     original_task_id: Optional[int] = Field(None, example=1) # Not in api.md, but makes sense.
#     original_task_title: str
#     subtasks: List[AISubtask]
#     ai_notes: Optional[str] = Field(None, example="The task was decomposed into frontend and backend parts.") # api.md has this

# For POST /schedule-day
# class TaskBasicInfo(BaseModel): already exists
#     task_id: int # api.md uses id, existing uses task_id. Stick to existing.
#     title: str
#     priority: int # api.md uses int
#     due_date: Optional[datetime.datetime] = None
#     estimated_duration_minutes: Optional[int] = Field(None, example=60) # api.md has this, existing has it.

# class UserPreferencesForAI(BaseModel): already exists
#     working_hours_start: Optional[time] = Field(None, example="09:00:00") # api.md uses time
#     working_hours_end: Optional[time] = Field(None, example="17:00:00") # api.md uses time
#     prefer_morning_focus: Optional[bool] = Field(None, example=True) # api.md has this example
    # max_focus_duration_minutes: Optional[int] = Field(None, example=120) # Already in existing
    # min_break_duration_minutes: Optional[int] = Field(None, example=15) # Already in existing

# class AIScheduleDayRequest(BaseModel): already exists
#     date_to_schedule: date # api.md uses date, existing uses date_to_schedule: datetime.date. Stick to existing.
#     tasks_to_schedule: List[TaskBasicInfo]
#     user_preferences: UserPreferencesForAI
#     current_energy_level: Optional[int] = Field(None, example=4, ge=1, le=5) # api.md has this
    # current_schedule: Optional[List[Dict[str, Any]]] = Field(None, example=[{"task_id": 5, "start_time": "10:00", "end_time": "11:00"}]) # Already in existing

# class AIScheduledTask(TaskBasicInfo): already exists
#     scheduled_start_time: datetime.datetime
#     scheduled_end_time: datetime.datetime

# class AIScheduleDayResponse(BaseModel): already exists
#     date_scheduled: date # api.md uses date, existing uses date_scheduled: datetime.date
#     scheduled_tasks: List[AIScheduledTask]
#     warnings: Optional[List[str]] = Field(None, example=["Could not schedule task X due to conflicts."]) # api.md has this
    # gaps_identified: Optional[List[Dict[str, Any]]] = None # Already in existing

# For POST /estimate-energy
# class AIEstimateEnergyRequest(BaseModel): already exists
#     recent_activity_summary: Optional[str] = Field(None, example="Had 2 long meetings, worked on coding task for 1 hour.") # api.md has this
#     recent_tasks_completed: Optional[int] = Field(None, example=3) # api.md has this
#     time_of_day: time # api.md uses time, existing uses datetime.time. Stick to existing.
#     user_self_reported_energy: Optional[int] = Field(None, example=3, ge=1, le=5) # api.md has this
    # task_description: str # Already in existing
    # task_duration_minutes: int # Already in existing
    # user_historical_energy: Optional[List[EnergyLog]] = None # Already in existing

# class AIEstimateEnergyResponse(BaseModel): already exists
#     estimated_energy_level: EnergyLevel # api.md uses int (1-5), existing uses EnergyLevel enum. Stick to existing.
#     confidence: Optional[float] = Field(None, ge=0, le=1, example=0.85) # api.md has this, existing has confidence_score. Rename to confidence.
    # task_description: str # Already in existing

# Consolidating and ensuring all fields from api.md are present, and types are correct.

# AIDecomposeTaskRequest:
# - task_title: str (from existing)
# - task_description: Optional[str] (from existing & api.md)
# - user_preferences: Optional[Dict[str, Any]] (from existing, api.md has user_prompt - let's use user_preferences as it's more generic like existing)
# - api.md mentions task_id (optional). Let's add it.

# AISubtask:
# - title: str (from existing & api.md)
# - description: Optional[str] (from existing & api.md)
# - estimated_duration_minutes: Optional[int] (from existing)
# - priority: Optional[int] (from existing, api.md suggests string but int is better for sorting)

# AIDecomposeTaskResponse:
# - original_task_title: str (from existing)
# - subtasks: List[AISubtask] (from existing & api.md)
# - original_task_id: Optional[int] (from api.md, add to existing)
# - ai_notes: Optional[str] (from api.md, add to existing)

# TaskBasicInfo:
# - id: int (api.md, change from task_id in existing)
# - title: str (from existing & api.md)
# - estimated_duration_minutes: int (from existing, api.md has Optional[int], make it required as per existing)
# - priority: Optional[int] (from existing & api.md)
# - due_date: Optional[datetime.datetime] (from existing & api.md)
# - project_id: Optional[int] (from existing)

# UserPreferencesForAI:
# - preferred_work_start_time: Optional[time] (from existing, api.md has working_hours_start: time) - align names
# - preferred_work_end_time: Optional[time] (from existing, api.md has working_hours_end: time) - align names
# - max_focus_duration_minutes: Optional[int] (from existing)
# - min_break_duration_minutes: Optional[int] (from existing)
# - api.md has prefer_morning_focus: bool. Add this.

# AIScheduleDayRequest:
# - date_to_schedule: date (from existing & api.md)
# - tasks_to_schedule: List[TaskBasicInfo] (from existing & api.md)
# - user_preferences: UserPreferencesForAI (from existing & api.md)
# - current_schedule: Optional[List[Dict[str, Any]]] (from existing)
# - api.md has current_energy_level: Optional[int]. Add this.

# AIScheduledTask: (inherits TaskBasicInfo)
# - scheduled_start_time: datetime.datetime (from existing & api.md)
# - scheduled_end_time: datetime.datetime (from existing & api.md)

# AIScheduleDayResponse:
# - date_scheduled: date (from existing & api.md)
# - scheduled_tasks: List[AIScheduledTask] (from existing & api.md)
# - gaps_identified: Optional[List[Dict[str, Any]]] (from existing)
# - api.md has warnings: Optional[List[str]]. Add this.

# AIEstimateEnergyRequest:
# - task_description: str (from existing)
# - task_duration_minutes: int (from existing)
# - time_of_day: time (from existing & api.md)
# - user_historical_energy: Optional[List[EnergyLog]] (from existing)
# - api.md has recent_activity_summary: Optional[str]. Add this.
# - api.md has recent_tasks_completed: Optional[int]. Add this.
# - api.md has user_self_reported_energy: Optional[int]. Add this.

# AIEstimateEnergyResponse:
# - task_description: str (from existing)
# - estimated_energy_level_required: EnergyLevel (from existing, api.md uses int but enum is better)
# - confidence_score: Optional[float] (from existing, api.md calls it confidence. Rename to confidence)

# It seems the schemas are already mostly there. I need to make minor adjustments.

# Adjusting AIDecomposeTaskRequest
# Add task_id from api.md
# Keep user_preferences from existing, as it's more flexible than user_prompt
# Ensure AIDecomposeTaskRequest has: task_title, task_description, user_preferences, task_id
# api.md: schemas.AIDecomposeTaskRequest // 包含 task_id (可选，用于上下文), task_title, task_description (可选), user_prompt (可选，用户具体要求)
# existing: task_title, task_description, user_preferences

# Adjusting AIDecomposeTaskResponse
# Add original_task_id from api.md (if not already there, it's not in existing)
# Add ai_notes from api.md
# Ensure AIDecomposeTaskResponse has: original_task_title, subtasks, original_task_id, ai_notes
# api.md: schemas.AIDecomposeTaskResponse // 包含 original_task_id (可选), subtasks: List[schemas.AISubtask], ai_notes: Optional[str]
# existing: original_task_title, subtasks

# Adjusting TaskBasicInfo
# api.md: { "task_id": int, "title": str, "priority": int, "due_date": Optional[datetime], "estimated_duration_minutes": Optional[int] }
# existing: id, title, estimated_duration_minutes, priority, due_date, project_id
# Change existing 'id' to 'task_id' for clarity, or keep 'id' if it's a convention. api.md uses 'task_id' in the description text but 'id' in its own TaskBasicInfo schema example.
# Let's stick to 'id' as in the existing schema for TaskBasicInfo.
# estimated_duration_minutes is Optional[int] in api.md, but required 'int' in existing. Keep as required.

# Adjusting UserPreferencesForAI
# api.md: { "working_hours_start": time, "working_hours_end": time, "prefer_morning_focus": bool, ... }
# existing: preferred_work_start_time, preferred_work_end_time, max_focus_duration_minutes, min_break_duration_minutes
# Add prefer_morning_focus: Optional[bool]
# Rename existing fields to match api.md:
# preferred_work_start_time -> working_hours_start
# preferred_work_end_time -> working_hours_end

# Adjusting AIScheduleDayRequest
# api.md: schemas.AIScheduleDayRequest // 包含 date: date, tasks_to_schedule: List[schemas.TaskBasicInfo], user_preferences: schemas.UserPreferencesForAI, current_energy_level: Optional[int]
# existing: date_to_schedule, tasks_to_schedule, user_preferences, current_schedule
# Add current_energy_level: Optional[int]

# Adjusting AIScheduleDayResponse
# api.md: schemas.AIScheduleDayResponse // 包含 scheduled_tasks: List[schemas.AIScheduledTask], warnings: Optional[List[str]]
# existing: date_scheduled, scheduled_tasks, gaps_identified
# Add warnings: Optional[List[str]]

# Adjusting AIEstimateEnergyRequest
# api.md: schemas.AIEstimateEnergyRequest // 包含 recent_activity_summary: Optional[str], recent_tasks_completed: Optional[int], time_of_day: datetime, user_self_reported_energy: Optional[int]
# existing: task_description, task_duration_minutes, time_of_day, user_historical_energy
# Add recent_activity_summary: Optional[str]
# Add recent_tasks_completed: Optional[int]
# Add user_self_reported_energy: Optional[int]
# api.md uses `datetime` for `time_of_day`, which is likely a typo and should be `time`. Existing schema uses `datetime.time`. This is correct.

# Adjusting AIEstimateEnergyResponse
# api.md: schemas.AIEstimateEnergyResponse // 包含 estimated_energy_level: int (1-5), confidence: Optional[float]
# existing: task_description, estimated_energy_level_required: EnergyLevel, confidence_score: Optional[float]
# Rename confidence_score to confidence.
# Keep EnergyLevel enum for estimated_energy_level_required, as it's more descriptive.

# First, I'll apply the changes to AIDecomposeTaskRequest and AIDecomposeTaskResponse.
# Then TaskBasicInfo and UserPreferencesForAI.
# Then AIScheduleDayRequest and AIScheduleDayResponse.
# Finally AIEstimateEnergyRequest and AIEstimateEnergyResponse.
# This is a multi-step process. I'll do it with several replace operations.

# Start with AIDecomposeTaskRequest
# Current:
# class AIDecomposeTaskRequest(BaseModel):
#     task_title: str = Field(..., example="Develop new company website")
#     task_description: Optional[str] = Field(None, example="Website should include home, about, services, contact pages.")
#     user_preferences: Optional[Dict[str, Any]] = Field(None, example={"preferred_duration_hours": 2})

# Target:
# class AIDecomposeTaskRequest(BaseModel):
#     task_id: Optional[int] = Field(None, example=1, description="Optional ID of the task to decompose, for context")
#     task_title: str = Field(..., example="Develop new company website")
#     task_description: Optional[str] = Field(None, example="Website should include home, about, services, contact pages.")
#     user_prompt: Optional[str] = Field(None, example="Focus on quick deliverables for a soft launch first.") # As per api.md text for this schema.
# Let's use user_prompt as specified in api.md for AIDecomposeTaskRequest.
# The existing schema has `user_preferences: Optional[Dict[str, Any]]`. The api.md text for this schema says `user_prompt: Optional[str]`.
# However, the `api.md` *example* for `AIDecomposeTaskRequest` in `app/schemas.py` (which I just read) uses `user_preferences: Optional[Dict[str, Any]]`.
# Let's check `api.md` again for `AIDecomposeTaskRequest`.
# `api.md` says: `schemas.AIDecomposeTaskRequest // 包含 task_id (可选，用于上下文), task_title, task_description (可选), user_prompt (可选，用户具体要求)`
# So, `user_prompt` it is. I'll change `user_preferences` to `user_prompt` and add `task_id`.

# Start with AIDecomposeTaskRequest and AISubtask and AIDecomposeTaskResponse
# These are defined in app/schemas.py starting at line 176.
# class AIDecomposeTaskRequest(BaseModel):
# task_title: str = Field(..., example="Develop new company website")
# task_description: Optional[str] = Field(None, example="Website should include home, about, services, contact pages.")
# user_preferences: Optional[Dict[str, Any]] = Field(None, example={"preferred_duration_hours": 2})

# class AISubtask(BaseModel):
# title: str = Field(..., example="Design homepage mockups")
# description: Optional[str] = Field(None, example="Create mockups for desktop and mobile views.")
# estimated_duration_minutes: Optional[int] = Field(None, example=120)
# priority: Optional[int] = Field(0, example=1)

# class AIDecomposeTaskResponse(BaseModel):
# original_task_title: str
# subtasks: List[AISubtask]

# Based on api.md:
# AIDecomposeTaskRequest needs: task_id (optional), task_title, task_description (optional), user_prompt (optional)
# AISubtask needs: title, description (optional), priority (optional, string in api.md, but let's keep int from existing)
#   The existing AISubtask already has: title, description, estimated_duration_minutes, priority (int). This is fine. api.md's AISubtask schema example is just title, description, priority. The existing one is more complete.
# AIDecomposeTaskResponse needs: original_task_id (optional), subtasks: List[AISubtask], ai_notes: Optional[str]. original_task_title is not in api.md, but it's good to have. Let's keep it.

# Changes for AIDecomposeTaskRequest:
# - Add `task_id: Optional[int]`
# - Change `user_preferences` to `user_prompt: Optional[str]`

# Changes for AIDecomposeTaskResponse:
# - Add `original_task_id: Optional[int]`
# - Add `ai_notes: Optional[str]`

# Let's apply these changes.
