"""
Meeting Assistant AI - FastAPI Backend
======================================
REST API for meeting transcription, summarization, and task extraction.
"""

import os
import sys
import json
import uuid
import shutil
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import httpx

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from speech_recognition import Transcriber
from summarization.llm_summarizer import LLMSummarizer
from action_item_extraction.ml_extractor import LLMActionItemExtractor

# Load environment variables
load_dotenv(Path(__file__).parent.parent.parent / ".env")

# Storage for processing jobs and results
jobs: Dict[str, Dict] = {}
results: Dict[str, Dict] = {}
jira_config: Dict[str, Any] = {}
user_mappings: Dict[str, str] = {}  # meeting_name -> jira_account_id

# Temp directory for uploads
UPLOAD_DIR = Path(__file__).parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Load saved configs if exist
    config_file = Path(__file__).parent / "config.json"
    if config_file.exists():
        with open(config_file, 'r') as f:
            data = json.load(f)
            jira_config.update(data.get('jira_config', {}))
            user_mappings.update(data.get('user_mappings', {}))
    yield
    # Save configs on shutdown
    with open(config_file, 'w') as f:
        json.dump({
            'jira_config': jira_config,
            'user_mappings': user_mappings
        }, f, indent=2)


app = FastAPI(
    title="Meeting Assistant AI",
    description="Transcribe meetings, generate summaries, and extract action items",
    version="1.0.0",
    lifespan=lifespan
)

# CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Pydantic Models
# ============================================================================

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


# ============================================================================
# Processing Functions
# ============================================================================

def process_meeting(job_id: str, file_path: Path, filename: str):
    """Background task to process meeting file"""
    start_time = datetime.now()
    
    try:
        # Step 1: Transcription
        jobs[job_id]["step"] = "transcription"
        jobs[job_id]["progress"] = 10
        jobs[job_id]["message"] = "Transcribing audio..."
        
        transcriber = Transcriber()
        transcript_result = transcriber.transcribe(str(file_path))
        
        jobs[job_id]["progress"] = 40
        jobs[job_id]["message"] = "Transcription complete. Generating summary..."
        
        # Convert to dict format
        transcript_data = {
            "metadata": {
                "file": filename,
                "duration": transcript_result.duration,
                "language": transcript_result.language
            },
            "transcript": [
                {
                    "speaker": f"Speaker_{i % 3:02d}",  # Assign speakers
                    "text": seg.text,
                    "start": seg.start,
                    "end": seg.end
                }
                for i, seg in enumerate(transcript_result.segments)
            ]
        }
        
        # Step 2: Summarization
        jobs[job_id]["step"] = "summarization"
        jobs[job_id]["progress"] = 50
        
        summarizer = LLMSummarizer()
        summary_result = summarizer.summarize(transcript_data)
        summary_dict = summarizer.to_dict(summary_result)
        
        jobs[job_id]["progress"] = 70
        jobs[job_id]["message"] = "Summary generated. Extracting tasks..."
        
        # Step 3: Task Extraction
        jobs[job_id]["step"] = "extraction"
        jobs[job_id]["progress"] = 80
        
        extractor = LLMActionItemExtractor()
        tasks_result = extractor.extract_action_items(transcript_data)
        
        # Convert tasks to our format with IDs
        tasks = []
        for i, task in enumerate(tasks_result.get('action_items', [])):
            task_item = TaskItem(
                id=f"{job_id}-task-{i}",
                description=task.get('description', ''),
                assignee=task.get('assignee'),
                due_date=task.get('due_date'),
                priority=task.get('priority', 'Medium'),
                speaker=task.get('speaker'),
                confidence=task.get('confidence')
            )
            # Try to auto-map assignee
            if task_item.assignee and task_item.assignee in user_mappings:
                task_item.jira_assignee_id = user_mappings[task_item.assignee]
            tasks.append(task_item)
        
        # Step 4: Complete
        jobs[job_id]["step"] = "done"
        jobs[job_id]["progress"] = 100
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["message"] = "Processing complete!"
        jobs[job_id]["completed_at"] = datetime.now().isoformat()
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # Store result
        results[job_id] = MeetingResult(
            job_id=job_id,
            filename=filename,
            duration=transcript_result.duration,
            language=transcript_result.language,
            transcript=[TranscriptSegment(**seg) for seg in transcript_data["transcript"]],
            summary=summary_dict,
            tasks=tasks,
            created_at=jobs[job_id]["created_at"],
            processing_time=processing_time
        ).model_dump()
        
    except Exception as e:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)
        jobs[job_id]["message"] = f"Error: {str(e)}"
        raise
    
    finally:
        # Cleanup uploaded file
        if file_path.exists():
            file_path.unlink()


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/")
async def root():
    return {"message": "Meeting Assistant AI API", "version": "1.0.0"}


@app.post("/api/upload", response_model=JobStatus)
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """Upload audio/video file and start processing"""
    
    # Validate file type
    allowed_extensions = {'.mp3', '.mp4', '.wav', '.m4a', '.webm', '.ogg', '.flac'}
    file_ext = Path(file.filename).suffix.lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
        )
    
    # Generate job ID
    job_id = str(uuid.uuid4())[:8]
    
    # Save file
    file_path = UPLOAD_DIR / f"{job_id}{file_ext}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Create job
    jobs[job_id] = {
        "job_id": job_id,
        "status": "processing",
        "step": "upload",
        "progress": 5,
        "message": "File uploaded. Starting transcription...",
        "created_at": datetime.now().isoformat(),
        "completed_at": None,
        "error": None
    }
    
    # Start background processing
    background_tasks.add_task(process_meeting, job_id, file_path, file.filename)
    
    return JobStatus(**jobs[job_id])


@app.get("/api/jobs/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str):
    """Get processing job status"""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobStatus(**jobs[job_id])


@app.get("/api/results/{job_id}")
async def get_results(job_id: str):
    """Get processing results"""
    if job_id not in results:
        if job_id in jobs and jobs[job_id]["status"] != "completed":
            raise HTTPException(status_code=202, detail="Still processing")
        raise HTTPException(status_code=404, detail="Results not found")
    return results[job_id]


@app.get("/api/results")
async def list_results():
    """List all available results"""
    return [
        {
            "job_id": r["job_id"],
            "filename": r["filename"],
            "created_at": r["created_at"],
            "duration": r["duration"],
            "task_count": len(r["tasks"])
        }
        for r in results.values()
    ]


@app.put("/api/results/{job_id}/tasks/{task_id}")
async def update_task(job_id: str, task_id: str, task: TaskItem):
    """Update a task item"""
    if job_id not in results:
        raise HTTPException(status_code=404, detail="Results not found")
    
    for i, t in enumerate(results[job_id]["tasks"]):
        if t["id"] == task_id:
            results[job_id]["tasks"][i] = task.model_dump()
            return task
    
    raise HTTPException(status_code=404, detail="Task not found")


# ============================================================================
# Jira Integration Endpoints
# ============================================================================

@app.post("/api/jira/config")
async def save_jira_config(config: JiraConfig):
    """Save Jira configuration"""
    jira_config.update(config.model_dump())
    
    # Test connection
    try:
        users = await fetch_jira_users()
        return {"status": "success", "message": f"Connected! Found {len(users)} users."}
    except Exception as e:
        jira_config.clear()
        raise HTTPException(status_code=400, detail=f"Connection failed: {str(e)}")


@app.get("/api/jira/config")
async def get_jira_config():
    """Get current Jira configuration (without token)"""
    if not jira_config:
        return {"configured": False}
    return {
        "configured": True,
        "domain": jira_config.get("domain"),
        "email": jira_config.get("email"),
        "project_key": jira_config.get("project_key")
    }


@app.delete("/api/jira/config")
async def delete_jira_config():
    """Delete Jira configuration"""
    jira_config.clear()
    return {"status": "success"}


async def fetch_jira_users() -> List[JiraUser]:
    """Fetch users from Jira"""
    if not jira_config:
        raise HTTPException(status_code=400, detail="Jira not configured")
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://{jira_config['domain']}/rest/api/3/users/search",
            auth=(jira_config['email'], jira_config['api_token']),
            params={"maxResults": 1000}
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Jira API error")
        
        users = []
        for user in response.json():
            if user.get('accountType') == 'atlassian':
                users.append(JiraUser(
                    account_id=user['accountId'],
                    display_name=user.get('displayName', ''),
                    email=user.get('emailAddress'),
                    avatar_url=user.get('avatarUrls', {}).get('48x48')
                ))
        return users


@app.get("/api/jira/users", response_model=List[JiraUser])
async def get_jira_users():
    """Get Jira users for assignment"""
    return await fetch_jira_users()


@app.post("/api/jira/user-mappings")
async def save_user_mapping(mapping: UserMapping):
    """Save meeting name to Jira user mapping"""
    user_mappings[mapping.meeting_name] = mapping.jira_account_id
    return {"status": "success"}


@app.get("/api/jira/user-mappings")
async def get_user_mappings():
    """Get all user mappings"""
    return user_mappings


@app.delete("/api/jira/user-mappings/{meeting_name}")
async def delete_user_mapping(meeting_name: str):
    """Delete a user mapping"""
    if meeting_name in user_mappings:
        del user_mappings[meeting_name]
    return {"status": "success"}


@app.post("/api/jira/create-issues")
async def create_jira_issues(request: JiraCreateRequest):
    """Create Jira issues from tasks"""
    if not jira_config:
        raise HTTPException(status_code=400, detail="Jira not configured")
    
    if request.job_id not in results:
        raise HTTPException(status_code=404, detail="Results not found")
    
    created_issues = []
    errors = []
    
    async with httpx.AsyncClient() as client:
        for task_draft in request.tasks:
            # Build Jira issue payload
            issue_data = {
                "fields": {
                    "project": {"key": jira_config["project_key"]},
                    "summary": task_draft.summary,
                    "description": {
                        "type": "doc",
                        "version": 1,
                        "content": [
                            {
                                "type": "paragraph",
                                "content": [
                                    {"type": "text", "text": task_draft.description}
                                ]
                            }
                        ]
                    },
                    "issuetype": {"name": task_draft.issue_type}
                }
            }
            
            # Add assignee if specified
            if task_draft.assignee_id:
                issue_data["fields"]["assignee"] = {"accountId": task_draft.assignee_id}
            
            # Add due date if specified
            if task_draft.due_date:
                issue_data["fields"]["duedate"] = task_draft.due_date
            
            # Add labels
            if task_draft.labels:
                issue_data["fields"]["labels"] = task_draft.labels
            
            try:
                response = await client.post(
                    f"https://{jira_config['domain']}/rest/api/3/issue",
                    auth=(jira_config['email'], jira_config['api_token']),
                    json=issue_data
                )
                
                if response.status_code == 201:
                    issue = response.json()
                    created_issues.append({
                        "task_id": task_draft.task_id,
                        "jira_key": issue["key"],
                        "jira_url": f"https://{jira_config['domain']}/browse/{issue['key']}"
                    })
                    
                    # Update task in results
                    for t in results[request.job_id]["tasks"]:
                        if t["id"] == task_draft.task_id:
                            t["jira_created"] = True
                            t["jira_key"] = issue["key"]
                            break
                else:
                    errors.append({
                        "task_id": task_draft.task_id,
                        "error": response.text
                    })
            except Exception as e:
                errors.append({
                    "task_id": task_draft.task_id,
                    "error": str(e)
                })
    
    return {
        "created": created_issues,
        "errors": errors,
        "success_count": len(created_issues),
        "error_count": len(errors)
    }


@app.get("/api/jira/projects")
async def get_jira_projects():
    """Get available Jira projects"""
    if not jira_config:
        raise HTTPException(status_code=400, detail="Jira not configured")
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://{jira_config['domain']}/rest/api/3/project",
            auth=(jira_config['email'], jira_config['api_token'])
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Jira API error")
        
        return [
            {"key": p["key"], "name": p["name"]}
            for p in response.json()
        ]


# ============================================================================
# Run Server
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
