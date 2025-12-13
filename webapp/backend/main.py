from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from config import CORS_ORIGINS
from database import create_tables
from routes import meetings, assignees, jira
from routes.auth import router as auth_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create database tables
    await create_tables()
    print("Database tables created/verified")
    yield
    # Shutdown: Nothing to do
    print("Shutting down...")


# Initialize FastAPI app
app = FastAPI(
    title="Meeting Assistant API",
    description="AI-powered meeting transcription, summarization, and task extraction",
    version="2.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(meetings.router, prefix="/api", tags=["Meetings"])
app.include_router(assignees.router, prefix="/api", tags=["Assignees"])
app.include_router(jira.router, prefix="/api/jira", tags=["Jira"])
