import uuid
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from config import ALLOWED_EXTENSIONS, UPLOAD_DIR
from database import get_db
from db_models import User, Meeting, Task
from models import JobStatus, TaskItem
from auth import get_current_user

router = APIRouter()

# In-memory job status tracking (for real-time updates during processing)
processing_jobs: Dict[str, dict] = {}


@router.post("/upload", response_model=JobStatus)
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    
    # Validate file type
    file_ext = Path(file.filename).suffix.lower()
    
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Generate job ID
    job_id = str(uuid.uuid4())[:8]
    
    # Save file
    file_path = UPLOAD_DIR / f"{job_id}{file_ext}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Create meeting record in database
    meeting = Meeting(
        job_id=job_id,
        user_id=current_user.id,
        filename=file.filename,
        status="processing",
        step="upload",
        progress=5,
        message="File uploaded. Starting transcription...",
    )
    db.add(meeting)
    await db.flush()
    
    # Track in memory for real-time updates
    processing_jobs[job_id] = {
        "job_id": job_id,
        "user_id": str(current_user.id),
        "meeting_id": str(meeting.id),
        "status": "processing",
        "step": "upload",
        "progress": 5,
        "message": "File uploaded. Starting transcription...",
        "created_at": meeting.created_at.isoformat(),
        "completed_at": None,
        "error": None
    }
    
    # Start background processing
    from services.meeting_processor import process_meeting_db
    # Use await instead of background_tasks for async function
    background_tasks.add_task(process_meeting_db, job_id, file_path, file.filename, str(current_user.id))
    
    # Commit database before background task
    await db.commit()
    
    return JobStatus(**{k: v for k, v in processing_jobs[job_id].items() if k not in ['user_id', 'meeting_id']})


@router.get("/jobs/{job_id}", response_model=JobStatus)
async def get_job_status(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # First check in-memory for active processing
    if job_id in processing_jobs:
        job = processing_jobs[job_id]
        if job["user_id"] != str(current_user.id):
            raise HTTPException(status_code=404, detail="Job not found")
        return JobStatus(**{k: v for k, v in job.items() if k not in ['user_id', 'meeting_id']})
    
    # Check database
    result = await db.execute(
        select(Meeting).where(
            Meeting.job_id == job_id,
            Meeting.user_id == current_user.id
        )
    )
    meeting = result.scalar_one_or_none()
    
    if not meeting:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return JobStatus(
        job_id=meeting.job_id,
        status=meeting.status,
        step=meeting.step,
        progress=meeting.progress,
        message=meeting.message or "",
        created_at=meeting.created_at.isoformat(),
        completed_at=meeting.completed_at.isoformat() if meeting.completed_at else None,
        error=meeting.error
    )


@router.get("/results/{job_id}")
async def get_results(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Meeting).where(
            Meeting.job_id == job_id,
            Meeting.user_id == current_user.id
        )
    )
    meeting = result.scalar_one_or_none()
    
    if not meeting:
        raise HTTPException(status_code=404, detail="Results not found")
    
    if meeting.status != "completed":
        raise HTTPException(status_code=202, detail="Still processing")
    
    # Get tasks
    tasks_result = await db.execute(
        select(Task).where(Task.meeting_id == meeting.id)
    )
    tasks = tasks_result.scalars().all()
    
    return {
        "job_id": meeting.job_id,
        "filename": meeting.filename,
        "duration": meeting.duration,
        "language": meeting.language,
        "transcript": meeting.transcript or [],
        "summary": meeting.summary or {},
        "tasks": [
            {
                "id": task.task_id,
                "description": task.description,
                "assignee": task.assignee,
                "due_date": task.due_date,
                "priority": task.priority,
                "speaker": task.speaker,
                "confidence": task.confidence,
                "jira_assignee_id": task.jira_assignee_id,
                "jira_created": task.jira_created,
                "jira_key": task.jira_key,
            }
            for task in tasks
        ],
        "created_at": meeting.created_at.isoformat(),
        "processing_time": meeting.processing_time,
    }


@router.get("/results")
async def list_results(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Query with LEFT JOIN to get task counts in a single query
    result = await db.execute(
        select(
            Meeting.job_id,
            Meeting.filename,
            Meeting.created_at,
            Meeting.duration,
            func.count(Task.id).label('task_count')
        )
        .outerjoin(Task, Meeting.id == Task.meeting_id)
        .where(
            Meeting.user_id == current_user.id,
            Meeting.status == "completed"
        )
        .group_by(Meeting.id, Meeting.job_id, Meeting.filename, Meeting.created_at, Meeting.duration)
        .order_by(Meeting.created_at.desc())
    )
    
    meeting_list = [
        {
            "job_id": row.job_id,
            "filename": row.filename,
            "created_at": row.created_at.isoformat(),
            "duration": row.duration,
            "task_count": row.task_count
        }
        for row in result.all()
    ]
    
    return meeting_list


@router.delete("/results/{job_id}")
async def delete_meeting(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Meeting).where(
            Meeting.job_id == job_id,
            Meeting.user_id == current_user.id
        )
    )
    meeting = result.scalar_one_or_none()
    
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    # Delete from database (cascade will delete tasks)
    await db.delete(meeting)
    
    # Clean up in-memory if exists
    if job_id in processing_jobs:
        del processing_jobs[job_id]
    
    # Delete uploaded files
    for file_path in UPLOAD_DIR.glob(f"{job_id}.*"):
        try:
            file_path.unlink()
        except Exception as e:
            print(f"Warning: Failed to delete file {file_path}: {e}")
    
    return {"status": "success", "message": "Meeting deleted"}


@router.put("/results/{job_id}/tasks/{task_id}")
async def update_task(
    job_id: str,
    task_id: str,
    task_update: TaskItem,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Verify meeting belongs to user
    meeting_result = await db.execute(
        select(Meeting).where(
            Meeting.job_id == job_id,
            Meeting.user_id == current_user.id
        )
    )
    meeting = meeting_result.scalar_one_or_none()
    
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    # Find and update task
    task_result = await db.execute(
        select(Task).where(
            Task.meeting_id == meeting.id,
            Task.task_id == task_id
        )
    )
    task = task_result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Update fields
    task.description = task_update.description
    task.assignee = task_update.assignee
    task.due_date = task_update.due_date
    task.priority = task_update.priority
    task.jira_assignee_id = task_update.jira_assignee_id
    task.jira_created = task_update.jira_created
    task.jira_key = task_update.jira_key
    
    await db.flush()
    
    return task_update
