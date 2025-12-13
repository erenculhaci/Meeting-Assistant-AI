from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class JobStatus(BaseModel):
    job_id: str
    status: str  # pending, processing, completed, failed
    step: str  # upload, transcription, summarization, extraction, done
    progress: int  # 0-100
    message: str
    created_at: str
    completed_at: Optional[str] = None
    error: Optional[str] = None


class TranscriptSegment(BaseModel):
    speaker: str
    text: str
    start: float
    end: float


class TaskItem(BaseModel):
    id: str
    description: str
    assignee: Optional[str] = None
    due_date: Optional[str] = None
    priority: Optional[str] = "Medium"
    speaker: Optional[str] = None
    confidence: Optional[float] = None
    jira_assignee_id: Optional[str] = None
    jira_created: bool = False
    jira_key: Optional[str] = None


class MeetingResult(BaseModel):
    job_id: str
    filename: str
    duration: float
    language: str
    transcript: List[TranscriptSegment]
    summary: Dict[str, Any]
    tasks: List[TaskItem]
    created_at: str
    processing_time: float


class JiraConfig(BaseModel):
    domain: str  # e.g., "yourcompany.atlassian.net"
    email: str
    api_token: str
    project_key: str


class JiraUser(BaseModel):
    account_id: str
    display_name: str
    email: Optional[str] = None
    avatar_url: Optional[str] = None


class UserMapping(BaseModel):
    meeting_name: str
    jira_account_id: str


class JiraTaskDraft(BaseModel):
    task_id: str
    summary: str
    description: str
    assignee_id: Optional[str] = None
    due_date: Optional[str] = None
    priority: str = "Medium"
    issue_type: str = "Task"
    labels: List[str] = []


class JiraCreateRequest(BaseModel):
    job_id: str
    tasks: List[JiraTaskDraft]
