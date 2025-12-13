"""
Jira Routes
===========
Endpoints for Jira integration - config, users, projects, issue creation.
"""

from typing import List
from fastapi import APIRouter, HTTPException
import httpx

from storage import jira_config, user_mappings, results
from models import JiraConfig, JiraUser, UserMapping, JiraCreateRequest

router = APIRouter()


@router.post("/config")
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


@router.get("/config")
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


@router.delete("/config")
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


@router.get("/users", response_model=List[JiraUser])
async def get_jira_users():
    """Get Jira users for assignment"""
    return await fetch_jira_users()


@router.post("/user-mappings")
async def save_user_mapping(mapping: UserMapping):
    """Save meeting name to Jira user mapping"""
    user_mappings[mapping.meeting_name] = mapping.jira_account_id
    return {"status": "success"}


@router.get("/user-mappings")
async def get_user_mappings():
    """Get all user mappings"""
    return user_mappings


@router.delete("/user-mappings/{meeting_name}")
async def delete_user_mapping(meeting_name: str):
    """Delete a user mapping"""
    if meeting_name in user_mappings:
        del user_mappings[meeting_name]
    return {"status": "success"}


@router.post("/create-issues")
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


@router.get("/projects")
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
