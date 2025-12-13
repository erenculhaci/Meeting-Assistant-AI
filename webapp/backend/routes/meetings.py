"""
Meeting Routes
==============
Upload, job status, results, and deletion endpoints.
"""

import uuid
import shutil
from pathlib import Path
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks

from config import ALLOWED_EXTENSIONS, UPLOAD_DIR
from storage import jobs, results, assignee_mappings
from models import JobStatus, TaskItem
from services.meeting_processor import process_meeting

router = APIRouter()


@router.post("/upload", response_model=JobStatus)
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """Upload audio/video file and start processing"""
    
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


@router.get("/jobs/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str):
    """Get processing job status"""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobStatus(**jobs[job_id])


@router.get("/results/{job_id}")
async def get_results(job_id: str):
    """Get processing results"""
    if job_id not in results:
        if job_id in jobs and jobs[job_id]["status"] != "completed":
            raise HTTPException(status_code=202, detail="Still processing")
        raise HTTPException(status_code=404, detail="Results not found")
    return results[job_id]


@router.get("/results")
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


@router.delete("/results/{job_id}")
async def delete_meeting(job_id: str):
    """Delete a meeting and its associated files"""
    if job_id not in results:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    # Delete the result data
    del results[job_id]
    
    # Delete from jobs if exists
    if job_id in jobs:
        del jobs[job_id]
    
    # Delete assignee mappings if exists
    if job_id in assignee_mappings:
        del assignee_mappings[job_id]
    
    # Delete uploaded files
    for file_path in UPLOAD_DIR.glob(f"{job_id}.*"):
        try:
            file_path.unlink()
        except Exception as e:
            print(f"Warning: Failed to delete file {file_path}: {e}")
    
    return {"status": "success", "message": "Meeting deleted"}


@router.put("/results/{job_id}/tasks/{task_id}")
async def update_task(job_id: str, task_id: str, task: TaskItem):
    """Update a task item"""
    if job_id not in results:
        raise HTTPException(status_code=404, detail="Results not found")
    
    for i, t in enumerate(results[job_id]["tasks"]):
        if t["id"] == task_id:
            results[job_id]["tasks"][i] = task.model_dump()
            return task
    
    raise HTTPException(status_code=404, detail="Task not found")
