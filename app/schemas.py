# Pydantic schemas for API request/response validation
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Dict, Any
import datetime
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

class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, example="Implement homepage UI")
    description: Optional[str] = Field(None, max_length=1000, example="Detail all sections and components.")
    due_date: Optional[datetime.datetime] = Field(None, example="2024-08-15T10:00:00Z")
    priority: Optional[int] = Field(0, ge=0, le=2, example=1) # 0:Low, 1:Medium, 2:High

class TagBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50, example="frontend")
    color: Optional[str] = Field(None, pattern=r"^#[0-9a-fA-F]{6}$", example="#FF5733")

class FocusSessionBase(BaseModel):
    task_id: Optional[int] = Field(None, example=1)
    start_time: datetime.datetime = Field(default_factory=datetime.datetime.utcnow, example="2024-07-21T14:30:00Z")
    notes: Optional[str] = Field(None, max_length=500, example="Initial thoughts on the task.")

class EnergyLogBase(BaseModel):
    energy_level: EnergyLevel = Field(..., example=EnergyLevel.MEDIUM)
    timestamp: datetime.datetime = Field(default_factory=datetime.datetime.utcnow, example="2024-07-21T09:00:00Z")
    notes: Optional[str] = Field(None, max_length=500, example="Feeling a bit tired after lunch.")


# --- Create Schemas (for POST requests) ---
class UserCreate(UserBase):
    password: str = Field(..., min_length=8, example="strongpassword123")

class ProjectCreate(ProjectBase):
    pass

class TaskCreate(TaskBase):
    project_id: int = Field(..., example=1)

class TagCreate(TagBase):
    pass

class FocusSessionCreate(FocusSessionBase):
    pass

class EnergyLogCreate(EnergyLogBase):
    pass


# --- Update Schemas (for PUT/PATCH requests) ---
class UserUpdate(BaseModel):
    email: Optional[EmailStr] = Field(None, example="new_user@example.com")
    username: Optional[str] = Field(None, min_length=3, max_length=50, example="johnny_doe")
    is_active: Optional[bool] = Field(None, example=True)

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
    created_at: datetime.datetime
    updated_at: datetime.datetime
    tags: List['Tag'] = [] # Use string literal for forward reference

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
    projects: List[Project] = []
    # tasks: List[Task] = [] # Tasks assigned to user

    class Config:
        orm_mode = True

class FocusSession(FocusSessionBase):
    id: int
    user_id: int
    end_time: Optional[datetime.datetime]
    status: FocusSessionStatus

    class Config:
        orm_mode = True

class EnergyLog(EnergyLogBase):
    id: int
    user_id: int

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
    task_id: int
    new_order: int # Or a 'previous_task_id' for linked-list style reordering

# --- AI Related Schemas ---
class AIDecomposeTaskRequest(BaseModel):
    task_title: str = Field(..., example="Develop new company website")
    task_description: Optional[str] = Field(None, example="Website should include home, about, services, contact pages.")
    user_preferences: Optional[Dict[str, Any]] = Field(None, example={"preferred_duration_hours": 2})

class AISubtask(BaseModel):
    title: str = Field(..., example="Design homepage mockups")
    description: Optional[str] = Field(None, example="Create mockups for desktop and mobile views.")
    estimated_duration_minutes: Optional[int] = Field(None, example=120)
    priority: Optional[int] = Field(0, example=1)

class AIDecomposeTaskResponse(BaseModel):
    original_task_title: str
    subtasks: List[AISubtask]

class TaskBasicInfo(BaseModel): # Used in AI scheduling
    id: int
    title: str
    estimated_duration_minutes: int # AI might add this or it's pre-existing
    priority: Optional[int] = 0
    due_date: Optional[datetime.datetime] = None
    project_id: Optional[int] = None # For context

class UserPreferencesForAI(BaseModel):
    preferred_work_start_time: Optional[datetime.time] = Field(None, example="09:00:00")
    preferred_work_end_time: Optional[datetime.time] = Field(None, example="17:00:00")
    max_focus_duration_minutes: Optional[int] = Field(None, example=120) # Max duration for a single task slot
    min_break_duration_minutes: Optional[int] = Field(None, example=15)

class AIScheduleDayRequest(BaseModel):
    date_to_schedule: datetime.date = Field(..., example="2024-07-22")
    tasks_to_schedule: List[TaskBasicInfo] # Tasks selected by user or pre-filtered
    user_preferences: UserPreferencesForAI
    current_schedule: Optional[List[Dict[str, Any]]] = Field(None, example=[{"task_id": 5, "start_time": "10:00", "end_time": "11:00"}]) # Existing commitments

class AIScheduledTask(TaskBasicInfo):
    scheduled_start_time: datetime.datetime
    scheduled_end_time: datetime.datetime

class AIScheduleDayResponse(BaseModel):
    date_scheduled: datetime.date
    scheduled_tasks: List[AIScheduledTask]
    gaps_identified: Optional[List[Dict[str, Any]]] = None # E.g., {"start_time": "12:00", "end_time": "13:00", "reason": "lunch break"}

class AIEstimateEnergyRequest(BaseModel):
    task_description: str
    task_duration_minutes: int
    time_of_day: datetime.time # e.g., "14:00"
    user_historical_energy: Optional[List[EnergyLog]] = None # simplified for example

class AIEstimateEnergyResponse(BaseModel):
    task_description: str
    estimated_energy_level_required: EnergyLevel
    confidence_score: Optional[float] = Field(None, ge=0, le=1)

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
# Python's `enum` and `datetime` are correctly imported and used.
# `pydantic.EmailStr` is used for email validation.
# `typing.Optional`, `List`, `Dict`, `Any` are used as needed.
# All schemas seem to be covered as per the request.
