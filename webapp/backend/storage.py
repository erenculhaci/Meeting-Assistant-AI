"""
Data Storage for Meeting Assistant AI
=====================================
In-memory storage with JSON persistence.
"""

import json
from typing import Dict, Any
from pathlib import Path
from config import CONFIG_FILE


# In-memory storage
jobs: Dict[str, Dict] = {}
results: Dict[str, Dict] = {}
jira_config: Dict[str, Any] = {}
user_mappings: Dict[str, str] = {}  # meeting_name -> jira_account_id
assignee_mappings: Dict[str, Dict[str, str]] = {}  # job_id -> {extracted_name: nickname}


def load_storage():
    """Load saved data from disk"""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r') as f:
            data = json.load(f)
            jira_config.update(data.get('jira_config', {}))
            user_mappings.update(data.get('user_mappings', {}))
            assignee_mappings.update(data.get('assignee_mappings', {}))


def save_storage():
    """Save data to disk"""
    with open(CONFIG_FILE, 'w') as f:
        json.dump({
            'jira_config': jira_config,
            'user_mappings': user_mappings,
            'assignee_mappings': assignee_mappings
        }, f, indent=2)
