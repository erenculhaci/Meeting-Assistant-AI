"""
Meeting Assistant AI - Main Application
=======================================
Modular FastAPI application for meeting transcription, summarization, and task extraction.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from config import CORS_ORIGINS
from storage import load_storage, save_storage
from routes import meetings, assignees, jira


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management"""
    # Startup: Load saved data
    load_storage()
    yield
    # Shutdown: Save data
    save_storage()


# Initialize FastAPI app
app = FastAPI(
    title="Meeting Assistant API",
    description="AI-powered meeting transcription, summarization, and task extraction",
    version="1.0.0",
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
app.include_router(meetings.router, prefix="/api", tags=["Meetings"])
app.include_router(assignees.router, prefix="/api", tags=["Assignees"])
app.include_router(jira.router, prefix="/api/jira", tags=["Jira"])
