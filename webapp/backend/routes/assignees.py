from typing import Optional, Dict
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_db
from db_models import User, Meeting, Task
from auth import get_current_user

router = APIRouter()


@router.get("/meetings/{job_id}/assignees")
async def get_assignee_mappings(
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
    
    # Get unique assignees from tasks
    tasks_result = await db.execute(
        select(Task).where(Task.meeting_id == meeting.id)
    )
    tasks = tasks_result.scalars().all()
    
    assignees = set()
    for task in tasks:
        if task.assignee and task.assignee.lower() != 'unassigned':
            assignees.add(task.assignee)
    
    # Return mappings with current nicknames
    stored_mappings = meeting.assignee_mappings or {}
    mappings = {}
    for assignee in sorted(assignees):
        mappings[assignee] = stored_mappings.get(assignee, None)
    
    return mappings


@router.put("/meetings/{job_id}/assignees")
async def update_assignee_mappings(
    job_id: str,
    mappings: Dict[str, Optional[str]],
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
    
    # Update mappings
    current_mappings = meeting.assignee_mappings or {}
    
    for name, nickname in mappings.items():
        if nickname is not None and nickname.strip():
            current_mappings[name] = nickname
        elif name in current_mappings:
            del current_mappings[name]
    
    meeting.assignee_mappings = current_mappings
    await db.flush()
    
    return {"status": "success", "mappings": current_mappings}
