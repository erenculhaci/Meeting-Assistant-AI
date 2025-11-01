"""
Example usage for action item extraction.
"""

from action_item_extraction.extractor import extract_action_items
from datetime import datetime

# Example 1: Basic usage
print("="*60)
print("Example 1: Basic Action Item Extraction")
print("="*60)

tasks = extract_action_items(
    transcript_file_path="outputs/transcript2.json",
    output_file="outputs/action_items.md",
    output_format="md",
    reference_date=datetime(2025, 11, 1)  # Meeting date
)

print(f"\nExtracted {len(tasks)} tasks")
print("\nSample tasks:")
for i, task in enumerate(tasks[:3], 1):
    print(f"\n{i}. {task['description']}")
    print(f"   Assignee: {task['assignee']}")
    if task.get('due_date_formatted'):
        print(f"   Due: {task['due_date_formatted']}")
    print(f"   Priority: {task['priority']}")

# Example 2: JSON output
print("\n" + "="*60)
print("Example 2: Extracting to JSON")
print("="*60)

tasks_json = extract_action_items(
    transcript_file_path="outputs/transcript2.json",
    output_file="outputs/action_items.json",
    output_format="json"
)

print(f"Saved {len(tasks_json)} tasks to JSON format")

# Example 3: Using the TaskExtractor directly for more control
print("\n" + "="*60)
print("Example 3: Direct TaskExtractor Usage")
print("="*60)

from action_item_extraction.core.task_extractor import TaskExtractor
import json

with open("outputs/transcript2.json", 'r', encoding='utf-8') as f:
    transcript_data = json.load(f)

extractor = TaskExtractor(reference_date=datetime(2025, 11, 1))
tasks = extractor.extract_tasks(transcript_data)

# Custom filtering
high_priority_tasks = [t for t in tasks if t['priority'] == 'high']
print(f"\nHigh priority tasks: {len(high_priority_tasks)}")

for task in high_priority_tasks:
    print(f"\n- {task['description']}")
    print(f"  Assigned to: {task['assignee']}")
    print(f"  Confidence: {task['confidence']:.0%}")
