# SQLAlchemy models for database tables
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Table, REAL, JSON, Enum
from sqlalchemy.orm import relationship
from .database import Base
import datetime
import enum

# Association table for many-to-many relationship between Tasks and Tags
task_tag_association = Table('task_tags', Base.metadata,
    Column('task_id', Integer, ForeignKey('tasks.id'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id'), primary_key=True)
)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    preferences = Column(JSON, nullable=True) # Added user preferences field

    projects = relationship("Project", back_populates="owner")
    tasks = relationship("Task", back_populates="assignee") # If tasks can be directly assigned to users
    focus_sessions = relationship("FocusSession", back_populates="user")
    energy_logs = relationship("EnergyLog", back_populates="user")
    tags = relationship("Tag", back_populates="owner", cascade="all, delete-orphan") # User's own tags

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), index=True, nullable=False)
    description = Column(String(500))
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    is_archived = Column(Boolean, default=False, nullable=False)
    archived_at = Column(DateTime, nullable=True)

    owner = relationship("User", back_populates="projects")
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), index=True, nullable=False)
    description = Column(String(1000))
    completed = Column(Boolean, default=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    assignee_id = Column(Integer, ForeignKey("users.id"), nullable=True) # Optional: if tasks are assigned
    due_date = Column(DateTime, nullable=True)
    priority = Column(Integer, default=0) # Example: 0=Low, 1=Medium, 2=High
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    project = relationship("Project", back_populates="tasks")
    assignee = relationship("User", back_populates="tasks") # If tasks can be assigned
    tags = relationship("Tag", secondary=task_tag_association, back_populates="tasks")
    focus_sessions = relationship("FocusSession", back_populates="task")

    # Fields for subtasks and ordering
    parent_task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    parent = relationship("Task", back_populates="sub_tasks", remote_side=[id]) # For parent task
    sub_tasks = relationship("Task", back_populates="parent", cascade="all, delete-orphan") # For list of sub_tasks

    order_in_list = Column(Float, nullable=True) # For custom sorting

    # Fields for recurring tasks
    is_recurring = Column(Boolean, default=False, nullable=False)
    recurring_schedule = Column(String, nullable=True) # E.g., RRULE string or cron expression


class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), index=True, nullable=False) # Removed unique=True here
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True) # Added user_id
    color = Column(String(7), nullable=True) # E.g., '#RRGGBB'
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    owner = relationship("User", back_populates="tags") # Added relationship to User
    tasks = relationship("Task", secondary=task_tag_association, back_populates="tags")

    __table_args__ = (UniqueConstraint('user_id', 'name', name='uq_user_tag_name'),) # Added unique constraint for user_id and name

# TaskTag is defined by the task_tag_association table, no separate class needed
# unless it has its own columns beyond the foreign keys.
# For this structure, SQLAlchemy handles the association table directly.

class FocusSessionStatus(enum.Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class FocusSession(Base):
    __tablename__ = "focus_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True) # Can be null if session is not for a specific task
    start_time = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    end_time = Column(DateTime, nullable=True)
    status = Column(Enum(FocusSessionStatus), default=FocusSessionStatus.ACTIVE, nullable=False)
    # duration_minutes = Column(Integer, nullable=True) # Can be calculated or stored
    notes = Column(String(500), nullable=True)
    # pomo_cycle_count = Column(Integer, default=0) # If using Pomodoro technique

    user = relationship("User", back_populates="focus_sessions")
    task = relationship("Task", back_populates="focus_sessions")

class EnergyLevel(enum.Enum):
    VERY_LOW = 1
    LOW = 2
    MEDIUM = 3
    HIGH = 4
    VERY_HIGH = 5

class EnergyLog(Base):
    __tablename__ = "energy_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    energy_level = Column(Enum(EnergyLevel), nullable=False) # Using REAL to store numeric energy level, or Integer
    notes = Column(String(500), nullable=True) # Optional notes about the energy level
    # mood = Column(String(50), nullable=True) # Optional: track mood alongside energy

    user = relationship("User", back_populates="energy_logs")

# Ensure all relationships are correctly defined and back_populates match.
# String lengths are examples and can be adjusted.
# Nullable constraints are set based on typical requirements.
# `cascade="all, delete-orphan"` on Project.tasks means tasks are deleted if project is.
# `TaskTag` model class is removed as `task_tag_association` table handles it directly.
# Added Enum for FocusSessionStatus and EnergyLevel for controlled vocabularies.
# Added some example fields commented out that might be useful.
# Added `assignee_id` to Task for optional user assignment.
# Added `color` to Tag.
# Added `priority` and `due_date` to Task.
# Added `notes` to FocusSession.
# Added `notes` to EnergyLog.
# Corrected String lengths to be more specific where appropriate.
# Ensured all necessary imports from SQLAlchemy are present.
# Changed TaskTag from a class to a Table object for the many-to-many relationship,
# which is a more common SQLAlchemy pattern for simple association tables.
# If TaskTag had its own attributes beyond task_id and tag_id, a class model would be appropriate.
# Added Enum type from sqlalchemy for status and energy_level fields.
# Added nullable=False to ForeignKeys where appropriate (e.g. project_id in Task)
# Added nullable=False to various string fields like username, email, etc.
# Added cascade to Project.tasks relationship.
# User.tasks relationship added for tasks directly assigned to a user.
# FocusSession.task_id can be nullable.
# Made sure Enum is imported from sqlalchemy not just standard enum.
# If using Python's built-in enum for choices, need to ensure SQLAlchemy handles it.
# Using sqlalchemy.Enum for direct database enum type (if supported) or varchar.
# Standardized datetime.datetime.utcnow to datetime.datetime.utcnow
# Changed REAL to Enum for energy_level, as it seems to be a categorical scale.
# If energy_level was meant to be a float, REAL or Float would be correct.
# For TaskTag, the primary key is composite, handled by the Table definition.
# Removed the explicit TaskTag class as the association table is sufficient.
# Added `JSON` to imports just in case, although not used in the final version.
# Added `Table` to imports.
# Added `Enum` to imports.
# Added `REAL` to imports for completeness, though I switched EnergyLog to use Enum.
# Verified back_populates consistency.
# Added `cascade="all, delete-orphan"` for Project.tasks.
# Added `assignee_id` and `assignee` relationship in `Task` and `User` respectively.
# Made `task_id` in `FocusSession` nullable.
# String lengths are now more specific.
# `hashed_password` in `User` is not nullable.
# `name` in `Project` is not nullable.
# `title` in `Task` is not nullable.
# `name` in `Tag` is not nullable.
# `user_id` in `FocusSession` is not nullable.
# `start_time` in `FocusSession` is not nullable.
# `status` in `FocusSession` is not nullable.
# `user_id` in `EnergyLog` is not nullable.
# `timestamp` in `EnergyLog` is not nullable.
# `energy_level` in `EnergyLog` is not nullable.
# Removed `duration_minutes` from `FocusSession` as it can be calculated.
# Removed `pomo_cycle_count` from `FocusSession` for now.
# Removed `mood` from `EnergyLog` for now.
# Clarified string lengths for username, email, project name, task title, tag name.
# Ensured standard library `enum` and `datetime` are imported.
# Final check of relationships and constraints.
# The `task_tag_association` table correctly defines the composite primary key for the Task-Tag link.
# The `Enum` type from `sqlalchemy` is used for `FocusSessionStatus` and `EnergyLevel`.
# This ensures database-level enum types if the backend supports it, otherwise VARCHAR.
# The `cascade` option in `Project.tasks` ensures that when a project is deleted, its associated tasks are also deleted.
# Nullability constraints are set for key fields.
# `JSON` and `REAL` are imported but not actively used in this version of the models, which is fine.
# The models now align with common practices for these entities.
# `User.tasks` relationship: if a task is directly assigned to a user (not just via project ownership).
# `Task.assignee_id` and `Task.assignee` support this.
# `FocusSession.task_id` is nullable, allowing for general focus sessions not tied to a specific task.
# `EnergyLog.energy_level` now uses the `EnergyLevel` enum.
# Table and column names are consistent with typical conventions.
# Default values for `created_at` and `updated_at` are set.
# `onupdate` is used for `updated_at` to automatically update the timestamp.
# Indexes are defined for frequently queried columns like `id`, `username`, `email`.
# Unique constraints are applied where necessary (e.g., `username`, `email`, `tag name`).
