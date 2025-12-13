"""
Assignee Routes
===============
Endpoints for managing task assignee nickname mappings.
"""

from typing import Optional, Dict
from fastapi import APIRouter, HTTPException

from storage import results, assignee_mappings

router = APIRouter()


@router.get("/meetings/{job_id}/assignees")
async def get_assignee_mappings(job_id: str):
    """Get assignee name mappings for a meeting's tasks"""
    if job_id not in results:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    # Get unique assignees from tasks
    assignees = set()
    for task in results[job_id]["tasks"]:
        assignee = task.get("assignee")
        if assignee and assignee.lower() != 'unassigned':
            assignees.add(assignee)
    
    # Return mappings with current nicknames
    mappings = {}
    for assignee in sorted(assignees):
        mappings[assignee] = assignee_mappings.get(job_id, {}).get(assignee, None)
    
    return mappings


@router.put("/meetings/{job_id}/assignees")
async def update_assignee_mappings(job_id: str, mappings: Dict[str, Optional[str]]):
    """Update assignee name mappings for a meeting's tasks (e.g., Emily -> emily22)"""
    if job_id not in results:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    # Update mappings
    if job_id not in assignee_mappings:
        assignee_mappings[job_id] = {}
    
    # Update only non-null values
    for name, nickname in mappings.items():
        if nickname is not None and nickname.strip():
            assignee_mappings[job_id][name] = nickname
        elif name in assignee_mappings[job_id]:
            # Remove mapping if cleared
            del assignee_mappings[job_id][name]
    
    return {"status": "success", "mappings": assignee_mappings[job_id]}
