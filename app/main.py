# FastAPI application entry point
from fastapi import FastAPI
from app.routers import auth, users, projects, tasks, tags # Removed focus_sessions, energy_logs, ai, monitoring
from app.database import engine, Base
# Ensure all models are imported for table creation, even if their routers are not present yet.
# This is important if Base.metadata.create_all() is to create these tables.
from app.models import User, Project, Task, Tag, FocusSession, EnergyLog

# Create database tables if they don't exist
# In a production app, you might use Alembic for migrations.
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="ZenithTask API",
    description="API for ZenithTask - a smart task and project management application with AI features.",
    version="0.1.0",
    # You can add more metadata like contact, license_info, etc.
    # openapi_tags can be used to group endpoints in the docs
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(projects.router, prefix="/api/projects", tags=["Projects"])
app.include_router(tasks.router, prefix="/api/tasks", tags=["Tasks"])
app.include_router(tags.router, prefix="/api/tags", tags=["Tags"])
# app.include_router(focus_sessions.router, prefix="/api/focus-sessions", tags=["Focus Sessions"]) # Removed
# app.include_router(energy_logs.router, prefix="/api/energy-logs", tags=["Energy Logs"]) # Removed
# app.include_router(ai.router, prefix="/api/ai", tags=["AI"]) # Removed
# app.include_router(monitoring.router, prefix="/api/monitoring", tags=["Monitoring"]) # Removed


@app.get("/", tags=["Root"])
async def root():
    return {"message": "Welcome to ZenithTask API. Navigate to /docs for API documentation."}
