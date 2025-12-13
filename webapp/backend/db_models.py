import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Text, Float, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from database import Base


class User(Base):
    __tablename__ = "users"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    meetings: Mapped[List["Meeting"]] = relationship("Meeting", back_populates="user", cascade="all, delete-orphan")
    jira_config: Mapped[Optional["JiraConfiguration"]] = relationship("JiraConfiguration", back_populates="user", uselist=False, cascade="all, delete-orphan")


class Meeting(Base):
    __tablename__ = "meetings"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Meeting metadata
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    duration: Mapped[float] = mapped_column(Float, default=0.0)
    language: Mapped[str] = mapped_column(String(50), default="unknown")
    processing_time: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Processing status
    status: Mapped[str] = mapped_column(String(50), default="processing")  # processing, completed, failed
    step: Mapped[str] = mapped_column(String(50), default="upload")  # upload, transcription, summarization, extraction, done
    progress: Mapped[int] = mapped_column(default=0)
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Results stored as JSON
    transcript: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # List of transcript segments
    summary: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # Summary dict
    
    # Assignee mappings for this meeting
    assignee_mappings: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, default=dict)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="meetings")
    tasks: Mapped[List["Task"]] = relationship("Task", back_populates="meeting", cascade="all, delete-orphan")


class Task(Base):
    __tablename__ = "tasks"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id: Mapped[str] = mapped_column(String(100), index=True, nullable=False)  # Original task ID from extraction
    meeting_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("meetings.id", ondelete="CASCADE"), nullable=False)
    
    # Task details
    description: Mapped[str] = mapped_column(Text, nullable=False)
    assignee: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    due_date: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    priority: Mapped[str] = mapped_column(String(50), default="Medium")
    speaker: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Jira integration
    jira_assignee_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    jira_created: Mapped[bool] = mapped_column(Boolean, default=False)
    jira_key: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    meeting: Mapped["Meeting"] = relationship("Meeting", back_populates="tasks")


class JiraConfiguration(Base):
    __tablename__ = "jira_configurations"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    # Jira settings
    domain: Mapped[str] = mapped_column(String(255), nullable=False)  # e.g., "yourcompany.atlassian.net"
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    api_token: Mapped[str] = mapped_column(String(500), nullable=False)  # Encrypted in production
    project_key: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # User mappings (meeting name -> jira account id)
    user_mappings: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, default=dict)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="jira_config")
