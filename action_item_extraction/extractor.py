import json
import os
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from dotenv import load_dotenv

from action_item_extraction.core.task_extractor import TaskExtractor
from action_item_extraction.ml_extractor import LLMActionItemExtractor

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


def extract_action_items(
    transcript_file_path: str = None,
    transcript_data: Dict = None,
    output_file: Optional[str] = None,
    output_format: str = 'json',
    reference_date: Optional[datetime] = None,
    use_llm: bool = False,  # NEW: Use pure LLM extraction
    use_llm_fallback: bool = False,  # OLD: Use LLM for clarification only
    llm_model: str = "llama-3.3-70b-versatile",
    llm_provider: str = "auto"  # "auto", "groq", "openai"
) -> Dict[str, Any]:
    """
    Extract action items from a meeting transcript.
    
    Args:
        transcript_file_path: Path to the transcript JSON file
        transcript_data: Direct transcript data (alternative to file path)
        output_file: Optional path to save the output
        output_format: Format for output ('json', 'md', 'txt')
        reference_date: Reference date for relative date parsing
        use_llm: Use pure LLM-based extraction (recommended)
        use_llm_fallback: Use LLM to clarify ambiguous tasks (rule-based + LLM)
        llm_model: LLM model to use
        llm_provider: LLM provider ("auto", "groq", "openai")
        
    Returns:
        Dictionary with extraction results
    """
    # Load transcript
    if transcript_data is None:
        if transcript_file_path is None:
            raise ValueError("Either transcript_file_path or transcript_data must be provided")
        logger.info(f"Loading transcript from {transcript_file_path}")
        with open(transcript_file_path, 'r', encoding='utf-8') as f:
            transcript_data = json.load(f)
    
    # Choose extraction method
    if use_llm:
        # Pure LLM extraction (few-shot learning)
        logger.info("Using LLM-based extraction (few-shot learning)")
        extractor = LLMActionItemExtractor(model=llm_model)
        result = extractor.extract_action_items(transcript_data)
        tasks = result.get('action_items', [])
    else:
        # Rule-based extraction with optional LLM clarification
        logger.info("Using rule-based extraction" + (" with LLM fallback" if use_llm_fallback else ""))
        extractor = TaskExtractor(
            reference_date=reference_date,
            use_llm_fallback=use_llm_fallback,
            llm_model=llm_model,
            llm_provider=llm_provider
        )
        tasks = extractor.extract_tasks(transcript_data)
        result = {
            'status': 'success',
            'action_items': tasks,
            'total_items': len(tasks),
            'extraction_method': 'rule_based' + ('_with_llm' if use_llm_fallback else '')
        }
    
    # Save if output file specified
    if output_file:
        if output_format == 'json':
            save_tasks_json(result, output_file)
        elif output_format == 'md':
            save_tasks_markdown(tasks, output_file)
        elif output_format == 'txt':
            save_tasks_text(tasks, output_file)
    
    return result


def save_tasks_json(result: Dict[str, Any], output_path: str) -> None:
    """Save tasks to JSON file."""
    logger.info(f"Saving tasks to JSON: {output_path}")
    
    tasks = result.get('action_items', [])
    
    # Convert datetime objects to strings for JSON serialization
    tasks_serializable = []
    for task in tasks:
        task_copy = task.copy()
        if task_copy.get('start_date'):
            if isinstance(task_copy['start_date'], datetime):
                task_copy['start_date'] = task_copy['start_date'].isoformat()
        if task_copy.get('due_date'):
            if isinstance(task_copy['due_date'], datetime):
                task_copy['due_date'] = task_copy['due_date'].isoformat()
        tasks_serializable.append(task_copy)
    
    output_data = {
        'status': result.get('status', 'success'),
        'task_count': len(tasks),
        'extracted_at': datetime.now().isoformat(),
        'extraction_method': result.get('extraction_method', 'unknown'),
        'tasks': tasks_serializable
    }
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Saved {len(tasks)} tasks to {output_path}")


def save_tasks_markdown(tasks: List[Dict[str, Any]], output_path: str) -> None:
    """Save tasks to Markdown file."""
    logger.info(f"Saving tasks to Markdown: {output_path}")
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# Action Items & Tasks\n\n")
        f.write(f"**Total Tasks**: {len(tasks)}\n\n")
        f.write(f"**Extracted**: {datetime.now().strftime('%B %d, %Y at %H:%M')}\n\n")
        f.write("---\n\n")
        
        if not tasks:
            f.write("*No action items were identified in this meeting.*\n")
            return
        
        # Group by priority
        high_priority = [t for t in tasks if t['priority'] == 'high']
        medium_priority = [t for t in tasks if t['priority'] == 'medium']
        low_priority = [t for t in tasks if t['priority'] == 'low']
        
        # High priority tasks
        if high_priority:
            f.write("## 🔴 High Priority Tasks\n\n")
            for i, task in enumerate(high_priority, 1):
                _write_task_markdown(f, task, i)
        
        # Medium priority tasks
        if medium_priority:
            f.write("## 🟡 Medium Priority Tasks\n\n")
            for i, task in enumerate(medium_priority, 1):
                _write_task_markdown(f, task, i)
        
        # Low priority tasks
        if low_priority:
            f.write("## 🟢 Low Priority Tasks\n\n")
            for i, task in enumerate(low_priority, 1):
                _write_task_markdown(f, task, i)
        
        # Summary table
        f.write("\n---\n\n")
        f.write("## Task Summary\n\n")
        f.write("| Task | Assignee | Due Date | Priority | Status |\n")
        f.write("|------|----------|----------|----------|--------|\n")
        
        for task in tasks:
            desc_short = task['description'][:50] + '...' if len(task['description']) > 50 else task['description']
            due_date = task.get('due_date_formatted', 'Not specified')
            assignee = task['assignee']
            priority = task['priority'].capitalize()
            status = task['status'].capitalize()
            
            f.write(f"| {desc_short} | {assignee} | {due_date} | {priority} | {status} |\n")
    
    logger.info(f"Saved {len(tasks)} tasks to {output_path}")


def _write_task_markdown(f, task: Dict[str, Any], index: int) -> None:
    """Write a single task in markdown format."""
    # Add urgency indicator
    urgency_icon = ''
    if task.get('urgency') == 'critical':
        urgency_icon = ' ⚠️ **URGENT**'
    elif task.get('urgency') == 'high':
        urgency_icon = ' ⏰'
    
    f.write(f"### Task {index}{urgency_icon}\n\n")
    f.write(f"**Description**: {task['description']}\n\n")
    f.write(f"- **Assignee**: {task['assignee']}\n")
    
    if task.get('due_date_formatted'):
        f.write(f"- **Due Date**: {task['due_date_formatted']}\n")
    
    if task.get('start_date_formatted'):
        f.write(f"- **Start Date**: {task['start_date_formatted']}\n")
    
    f.write(f"- **Priority**: {task['priority'].capitalize()}\n")
    
    if task.get('urgency') != 'normal':
        f.write(f"- **Urgency**: {task['urgency'].capitalize()}\n")
    
    f.write(f"- **Type**: {task['type'].replace('_', ' ').title()}\n")
    f.write(f"- **Confidence**: {task['confidence']:.0%}\n")
    f.write(f"- **Status**: {task['status'].replace('_', ' ').title()}\n")
    
    if task.get('is_important'):
        f.write(f"- **⭐ Marked as Important**\n")
    
    if task.get('mentioned_dates'):
        f.write(f"- **Related Dates**: {', '.join(task['mentioned_dates'])}\n")
    
    f.write(f"\n**Source**: *\"{task['source_text']}\"*\n\n")
    f.write("---\n\n")


def save_tasks_text(tasks: List[Dict[str, Any]], output_path: str) -> None:
    """Save tasks to plain text file."""
    logger.info(f"Saving tasks to text: {output_path}")
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("ACTION ITEMS & TASKS\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Total Tasks: {len(tasks)}\n")
        f.write(f"Extracted: {datetime.now().strftime('%B %d, %Y at %H:%M')}\n\n")
        
        if not tasks:
            f.write("No action items were identified in this meeting.\n")
            return
        
        for i, task in enumerate(tasks, 1):
            f.write("-" * 80 + "\n")
            f.write(f"TASK #{i}\n")
            f.write("-" * 80 + "\n\n")
            f.write(f"Description: {task['description']}\n")
            f.write(f"Assignee: {task['assignee']}\n")
            f.write(f"Priority: {task['priority'].upper()}\n")
            f.write(f"Type: {task['type'].replace('_', ' ').title()}\n")
            f.write(f"Status: {task['status'].capitalize()}\n")
            
            if task.get('due_date_formatted'):
                f.write(f"Due Date: {task['due_date_formatted']}\n")
            
            if task.get('start_date_formatted'):
                f.write(f"Start Date: {task['start_date_formatted']}\n")
            
            f.write(f"Confidence: {task['confidence']:.0%}\n")
            f.write(f"\nSource: \"{task['source_text']}\"\n\n")
    
    logger.info(f"Saved {len(tasks)} tasks to {output_path}")
