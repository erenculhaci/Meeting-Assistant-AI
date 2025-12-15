from typing import List
from datetime import datetime, timedelta
import re
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import httpx

from database import get_db
from db_models import User, Meeting, Task, JiraConfiguration
from models import JiraConfig, JiraUser, UserMapping, JiraCreateRequest
from auth import get_current_user

router = APIRouter()


# Day name mappings
DAY_NAMES = {
    'monday': 0, 'mon': 0,
    'tuesday': 1, 'tue': 1, 'tues': 1,
    'wednesday': 2, 'wed': 2,
    'thursday': 3, 'thu': 3, 'thur': 3, 'thurs': 3,
    'friday': 4, 'fri': 4,
    'saturday': 5, 'sat': 5,
    'sunday': 6, 'sun': 6,
}


def get_next_weekday(reference_date: datetime, target_weekday: int, next_week: bool = False) -> datetime:
    current_weekday = reference_date.weekday()
    days_ahead = target_weekday - current_weekday
    
    if days_ahead <= 0:  # Target day already happened this week
        days_ahead += 7
    
    if next_week:
        days_ahead += 7
    
    return reference_date + timedelta(days=days_ahead)


def normalize_date_to_jira_format(date_str: str, reference_date: datetime = None) -> str:
    """
    Convert various date formats to Jira's required yyyy-MM-dd format.
    Handles vague dates like "Saturday", "next Monday", "tomorrow", etc.
    
    For example: 
      - "December 20" -> "2025-12-20"
      - "Dec 20, 2025" -> "2025-12-20"
      - "Saturday" -> next Saturday from today
      - "next Monday" -> Monday of next week
      - "tomorrow" -> today + 1
      - "this Friday" -> this week's Friday
    """
    if not date_str:
        return None
    
    if reference_date is None:
        reference_date = datetime.now()
    
    date_lower = date_str.lower().strip()
    
    # Already in correct format
    if re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
        return date_str
    
    # Handle "tonight", "this night", "today"
    if date_lower in ['tonight', 'this night', 'today', 'bugün', 'bu gece']:
        return reference_date.strftime("%Y-%m-%d")
    
    # Handle "tomorrow", "yarın"
    if date_lower in ['tomorrow', 'yarın', 'yarin']:
        return (reference_date + timedelta(days=1)).strftime("%Y-%m-%d")
    
    # Handle "next week", "gelecek hafta"
    if date_lower in ['next week', 'gelecek hafta', 'haftaya']:
        return (reference_date + timedelta(days=7)).strftime("%Y-%m-%d")
    
    # Handle "end of week", "hafta sonu"
    if date_lower in ['end of week', 'end of the week', 'eow']:
        # Find next Friday
        return get_next_weekday(reference_date, 4).strftime("%Y-%m-%d")
    
    # Handle "weekend", "hafta sonu"
    if date_lower in ['weekend', 'this weekend', 'hafta sonu', 'haftasonu']:
        return get_next_weekday(reference_date, 5).strftime("%Y-%m-%d")  # Saturday
    
    # Handle "next [day]" pattern
    next_match = re.match(r'^next\s+(\w+)', date_lower)
    if next_match:
        day_name = next_match.group(1).lower()
        # Remove "night", "morning", etc.
        day_name = re.sub(r'\s*(night|morning|evening|afternoon)$', '', day_name)
        if day_name in DAY_NAMES:
            return get_next_weekday(reference_date, DAY_NAMES[day_name], next_week=True).strftime("%Y-%m-%d")
    
    # Handle "this [day]" pattern
    this_match = re.match(r'^this\s+(\w+)', date_lower)
    if this_match:
        day_name = this_match.group(1).lower()
        day_name = re.sub(r'\s*(night|morning|evening|afternoon)$', '', day_name)
        if day_name in DAY_NAMES:
            return get_next_weekday(reference_date, DAY_NAMES[day_name]).strftime("%Y-%m-%d")
    
    # Handle standalone day names: "Saturday", "Monday night", "Friday evening"
    for day_pattern, weekday_num in DAY_NAMES.items():
        # Match day name with optional time of day suffix
        pattern = rf'^{day_pattern}(\s*(night|morning|evening|afternoon|noon))?$'
        if re.match(pattern, date_lower):
            return get_next_weekday(reference_date, weekday_num).strftime("%Y-%m-%d")
    
    # Handle "in X days"
    in_days_match = re.match(r'^in\s+(\d+)\s+days?$', date_lower)
    if in_days_match:
        days = int(in_days_match.group(1))
        return (reference_date + timedelta(days=days)).strftime("%Y-%m-%d")
    
    # Handle "in X weeks"
    in_weeks_match = re.match(r'^in\s+(\d+)\s+weeks?$', date_lower)
    if in_weeks_match:
        weeks = int(in_weeks_match.group(1))
        return (reference_date + timedelta(weeks=weeks)).strftime("%Y-%m-%d")
    
    # Try various explicit date formats
    date_formats = [
        "%B %d, %Y",      # December 20, 2025
        "%B %d",          # December 20
        "%b %d, %Y",      # Dec 20, 2025
        "%b %d",          # Dec 20
        "%d %B %Y",       # 20 December 2025
        "%d %B",          # 20 December
        "%d/%m/%Y",       # 20/12/2025
        "%m/%d/%Y",       # 12/20/2025
        "%d-%m-%Y",       # 20-12-2025
        "%Y/%m/%d",       # 2025/12/20
        "%d.%m.%Y",       # 20.12.2025
    ]
    
    current_year = reference_date.year
    
    for fmt in date_formats:
        try:
            parsed = datetime.strptime(date_str.strip(), fmt)
            # If no year in format, use current year
            if parsed.year == 1900:
                parsed = parsed.replace(year=current_year)
                # If the date has already passed this year, use next year
                if parsed < reference_date:
                    parsed = parsed.replace(year=current_year + 1)
            return parsed.strftime("%Y-%m-%d")
        except ValueError:
            continue
    
    # If still can't parse, return None (will be skipped in Jira creation)
    return None


def find_best_matching_user(assignee_name: str, jira_users: List[dict]) -> str:
    if not assignee_name or not jira_users:
        return None
    
    assignee_lower = assignee_name.lower().strip()
    
    # First, try exact match
    for user in jira_users:
        display_name = (user.get('displayName') or '').lower()
        if display_name == assignee_lower:
            return user.get('accountId')
    
    # Then, try partial match (name contains assignee or vice versa)
    best_match = None
    best_score = 0
    
    for user in jira_users:
        display_name = (user.get('displayName') or '').lower()
        
        # Check if first name matches
        assignee_parts = assignee_lower.split()
        display_parts = display_name.split()
        
        for a_part in assignee_parts:
            for d_part in display_parts:
                # Exact word match
                if a_part == d_part and len(a_part) > 2:
                    score = len(a_part) * 2
                    if score > best_score:
                        best_score = score
                        best_match = user.get('accountId')
                # Partial match (starts with)
                elif d_part.startswith(a_part) or a_part.startswith(d_part):
                    score = min(len(a_part), len(d_part))
                    if score > best_score and score >= 3:
                        best_score = score
                        best_match = user.get('accountId')
    
    return best_match


@router.post("/config")
async def save_jira_config(
    config: JiraConfig,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
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
    result = await db.execute(
        select(JiraConfiguration).where(JiraConfiguration.user_id == current_user.id)
    )
    jira_conf = result.scalar_one_or_none()
    
    if jira_conf:
        await db.delete(jira_conf)
    
    return {"status": "success"}


async def fetch_jira_users_internal(jira_conf: JiraConfiguration) -> List[JiraUser]:
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
    
    # Get assignee mappings from the meeting
    assignee_mappings = meeting.assignee_mappings or {}
    
    # Fetch Jira users for auto-assignment
    jira_users = []
    async with httpx.AsyncClient() as client:
        try:
            users_response = await client.get(
                f"https://{jira_conf.domain}/rest/api/3/users/search?maxResults=1000",
                auth=(jira_conf.email, jira_conf.api_token)
            )
            if users_response.status_code == 200:
                jira_users = users_response.json()
        except:
            pass
    
    # Fetch all tasks for this meeting at once to prevent N+1
    all_tasks_result = await db.execute(
        select(Task).where(Task.meeting_id == meeting.id)
    )
    tasks_by_id = {task.task_id: task for task in all_tasks_result.scalars().all()}
    
    created_issues = []
    errors = []
    
    async with httpx.AsyncClient() as client:
        for task_draft in request.tasks:
            # Normalize due date to yyyy-MM-dd format
            normalized_due_date = None
            if task_draft.due_date:
                normalized_due_date = normalize_date_to_jira_format(task_draft.due_date)
            
            # Auto-find assignee if not specified
            assignee_id = task_draft.assignee_id
            if not assignee_id and task_draft.description:
                # Try to extract name from description
                extracted_name = task_draft.description.split(':')[0] if ':' in task_draft.description else None
                
                # Apply nickname mapping if available
                if extracted_name and extracted_name in assignee_mappings:
                    mapped_name = assignee_mappings[extracted_name]
                    assignee_id = find_best_matching_user(mapped_name, jira_users)
                else:
                    # Use original name if no mapping
                    assignee_id = find_best_matching_user(extracted_name, jira_users)
            
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
            if assignee_id:
                issue_data["fields"]["assignee"] = {"accountId": assignee_id}
            
            # Add due date if specified and valid
            if normalized_due_date:
                issue_data["fields"]["duedate"] = normalized_due_date
            
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
                    
                    # Update task in database using pre-fetched dictionary
                    task = tasks_by_id.get(task_draft.task_id)
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


@router.post("/verify-tasks/{job_id}")
async def verify_jira_tasks(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Verify which tasks still exist in Jira and update their status accordingly.
    Returns updated task statuses.
    """
    # Get Jira config
    config_result = await db.execute(
        select(JiraConfiguration).where(JiraConfiguration.user_id == current_user.id)
    )
    jira_conf = config_result.scalar_one_or_none()
    
    if not jira_conf:
        raise HTTPException(status_code=400, detail="Jira not configured")
    
    # Get meeting and its tasks
    meeting_result = await db.execute(
        select(Meeting).where(
            Meeting.job_id == job_id,
            Meeting.user_id == current_user.id
        )
    )
    meeting = meeting_result.scalar_one_or_none()
    
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    # Get all tasks that were marked as created in Jira
    tasks_result = await db.execute(
        select(Task).where(
            Task.meeting_id == meeting.id,
            Task.jira_created == True
        )
    )
    tasks = tasks_result.scalars().all()
    
    updated_count = 0
    async with httpx.AsyncClient() as client:
        for task in tasks:
            if not task.jira_key:
                continue
                
            try:
                # Check if the issue still exists in Jira
                response = await client.get(
                    f"https://{jira_conf.domain}/rest/api/3/issue/{task.jira_key}",
                    auth=(jira_conf.email, jira_conf.api_token)
                )
                
                # If issue doesn't exist (404), mark as not created
                if response.status_code == 404:
                    task.jira_created = False
                    task.jira_key = None
                    updated_count += 1
            except:
                # On any error, assume the issue is gone
                task.jira_created = False
                task.jira_key = None
                updated_count += 1
    
    return {
        "status": "success",
        "updated_count": updated_count,
        "message": f"Verified {len(tasks)} tasks, updated {updated_count}"
    }
