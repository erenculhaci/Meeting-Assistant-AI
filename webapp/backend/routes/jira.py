"""
Jira Routes
===========
Endpoints for Jira integration - config, users, projects, issue creation.
All endpoints are user-aware and use PostgreSQL storage.
"""

from typing import List
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import httpx

from database import get_db
from db_models import User, Meeting, Task, JiraConfiguration
from models import JiraConfig, JiraUser, UserMapping, JiraCreateRequest
from auth import get_current_user

router = APIRouter()


@router.post("/config")
async def save_jira_config(
    config: JiraConfig,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Save Jira configuration for current user"""
    # Check if config exists
    result = await db.execute(
        select(JiraConfiguration).where(JiraConfiguration.user_id == current_user.id)
    )
    jira_conf = result.scalar_one_or_none()
    
    if jira_conf:
        # Update existing
        jira_conf.domain = config.domain
        jira_conf.email = config.email
        jira_conf.api_token = config.api_token
        jira_conf.project_key = config.project_key
    else:
        # Create new
        jira_conf = JiraConfiguration(
            user_id=current_user.id,
            domain=config.domain,
            email=config.email,
            api_token=config.api_token,
            project_key=config.project_key,
        )
        db.add(jira_conf)
    
    await db.flush()
    
    # Test connection
    try:
        users = await fetch_jira_users_internal(jira_conf)
        return {"status": "success", "message": f"Connected! Found {len(users)} users."}
    except Exception as e:
        # Rollback on failure
        await db.delete(jira_conf)
        raise HTTPException(status_code=400, detail=f"Connection failed: {str(e)}")


@router.get("/config")
async def get_jira_config(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current user's Jira configuration (without token)"""
    result = await db.execute(
        select(JiraConfiguration).where(JiraConfiguration.user_id == current_user.id)
    )
    jira_conf = result.scalar_one_or_none()
    
    if not jira_conf:
        return {"configured": False}
    
    return {
        "configured": True,
        "domain": jira_conf.domain,
        "email": jira_conf.email,
        "project_key": jira_conf.project_key
    }


@router.delete("/config")
async def delete_jira_config(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete current user's Jira configuration"""
    result = await db.execute(
        select(JiraConfiguration).where(JiraConfiguration.user_id == current_user.id)
    )
    jira_conf = result.scalar_one_or_none()
    
    if jira_conf:
        await db.delete(jira_conf)
    
    return {"status": "success"}


async def fetch_jira_users_internal(jira_conf: JiraConfiguration) -> List[JiraUser]:
    """Fetch users from Jira using stored configuration"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://{jira_conf.domain}/rest/api/3/users/search",
            auth=(jira_conf.email, jira_conf.api_token),
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


@router.get("/users", response_model=List[JiraUser])
async def get_jira_users(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get Jira users for assignment"""
    result = await db.execute(
        select(JiraConfiguration).where(JiraConfiguration.user_id == current_user.id)
    )
    jira_conf = result.scalar_one_or_none()
    
    if not jira_conf:
        raise HTTPException(status_code=400, detail="Jira not configured")
    
    return await fetch_jira_users_internal(jira_conf)


@router.post("/user-mappings")
async def save_user_mapping(
    mapping: UserMapping,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Save meeting name to Jira user mapping"""
    result = await db.execute(
        select(JiraConfiguration).where(JiraConfiguration.user_id == current_user.id)
    )
    jira_conf = result.scalar_one_or_none()
    
    if not jira_conf:
        raise HTTPException(status_code=400, detail="Jira not configured")
    
    current_mappings = jira_conf.user_mappings or {}
    current_mappings[mapping.meeting_name] = mapping.jira_account_id
    jira_conf.user_mappings = current_mappings
    
    await db.flush()
    return {"status": "success"}


@router.get("/user-mappings")
async def get_user_mappings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all user mappings"""
    result = await db.execute(
        select(JiraConfiguration).where(JiraConfiguration.user_id == current_user.id)
    )
    jira_conf = result.scalar_one_or_none()
    
    if not jira_conf:
        return {}
    
    return jira_conf.user_mappings or {}


@router.delete("/user-mappings/{meeting_name}")
async def delete_user_mapping(
    meeting_name: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a user mapping"""
    result = await db.execute(
        select(JiraConfiguration).where(JiraConfiguration.user_id == current_user.id)
    )
    jira_conf = result.scalar_one_or_none()
    
    if jira_conf and jira_conf.user_mappings:
        if meeting_name in jira_conf.user_mappings:
            del jira_conf.user_mappings[meeting_name]
            await db.flush()
    
    return {"status": "success"}


@router.post("/create-issues")
async def create_jira_issues(
    request: JiraCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create Jira issues from tasks"""
    # Get Jira config
    config_result = await db.execute(
        select(JiraConfiguration).where(JiraConfiguration.user_id == current_user.id)
    )
    jira_conf = config_result.scalar_one_or_none()
    
    if not jira_conf:
        raise HTTPException(status_code=400, detail="Jira not configured")
    
    # Verify meeting belongs to user
    meeting_result = await db.execute(
        select(Meeting).where(
            Meeting.job_id == request.job_id,
            Meeting.user_id == current_user.id
        )
    )
    meeting = meeting_result.scalar_one_or_none()
    
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    created_issues = []
    errors = []
    
    async with httpx.AsyncClient() as client:
        for task_draft in request.tasks:
            # Build Jira issue payload
            issue_data = {
                "fields": {
                    "project": {"key": jira_conf.project_key},
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
                    f"https://{jira_conf.domain}/rest/api/3/issue",
                    auth=(jira_conf.email, jira_conf.api_token),
                    json=issue_data,
                    headers={"Accept": "application/json", "Content-Type": "application/json"}
                )
                
                if response.status_code == 201:
                    issue = response.json()
                    created_issues.append({
                        "task_id": task_draft.task_id,
                        "jira_key": issue["key"],
                        "jira_url": f"https://{jira_conf.domain}/browse/{issue['key']}"
                    })
                    
                    # Update task in database
                    task_result = await db.execute(
                        select(Task).where(
                            Task.meeting_id == meeting.id,
                            Task.task_id == task_draft.task_id
                        )
                    )
                    task = task_result.scalar_one_or_none()
                    if task:
                        task.jira_created = True
                        task.jira_key = issue["key"]
                else:
                    error_detail = response.text
                    try:
                        error_json = response.json()
                        error_detail = str(error_json)
                    except:
                        pass
                    
                    errors.append({
                        "task_id": task_draft.task_id,
                        "summary": task_draft.summary,
                        "error": error_detail,
                        "status_code": response.status_code
                    })
            except Exception as e:
                errors.append({
                    "task_id": task_draft.task_id,
                    "summary": task_draft.summary,
                    "error": str(e)
                })
    
    await db.flush()
    
    return {
        "created": created_issues,
        "errors": errors,
        "success_count": len(created_issues),
        "error_count": len(errors)
    }


@router.get("/projects")
async def get_jira_projects(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get available Jira projects"""
    result = await db.execute(
        select(JiraConfiguration).where(JiraConfiguration.user_id == current_user.id)
    )
    jira_conf = result.scalar_one_or_none()
    
    if not jira_conf:
        raise HTTPException(status_code=400, detail="Jira not configured")
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://{jira_conf.domain}/rest/api/3/project",
            auth=(jira_conf.email, jira_conf.api_token)
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Jira API error")
        
        return [
            {"key": p["key"], "name": p["name"]}
            for p in response.json()
        ]
