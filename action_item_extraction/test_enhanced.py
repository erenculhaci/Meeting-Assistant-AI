"""
Test the enhanced action item extraction module.
"""

import sys
import os
from datetime import datetime

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from action_item_extraction.extractor import extract_action_items

print("="*80)
print("ENHANCED ACTION ITEM EXTRACTION TEST")
print("="*80)

print("\nTesting with enhanced features:")
print("- Expanded task patterns (45+ patterns)")
print("- Urgency detection (ASAP, urgent, critical)")
print("- Confidence scoring model")
print("- Semantic deduplication")
print("- Advanced date parsing")
print("="*80)

# Use absolute path
input_file = os.path.join(project_root, "outputs", "transcription", "transcript2.json")
output_file = os.path.join(project_root, "outputs", "action_items", "action_items_enhanced.md")

# Test with semantic deduplication
tasks = extract_action_items(
    transcript_file_path=input_file,
    output_file=output_file,
    output_format="md",
    reference_date=datetime(2025, 11, 1)
)

print(f"\n✅ Extracted {len(tasks)} tasks")

# Show statistics
urgency_counts = {}
priority_counts = {}
status_counts = {}

for task in tasks:
    urgency = task.get('urgency', 'normal')
    priority = task['priority']
    status = task['status']
    
    urgency_counts[urgency] = urgency_counts.get(urgency, 0) + 1
    priority_counts[priority] = priority_counts.get(priority, 0) + 1
    status_counts[status] = status_counts.get(status, 0) + 1

print("\n📊 Task Statistics:")
print(f"\nBy Urgency:")
for urgency, count in sorted(urgency_counts.items()):
    print(f"  - {urgency.capitalize()}: {count}")

print(f"\nBy Priority:")
for priority, count in sorted(priority_counts.items()):
    print(f"  - {priority.capitalize()}: {count}")

print(f"\nBy Status:")
for status, count in sorted(status_counts.items()):
    print(f"  - {status.replace('_', ' ').capitalize()}: {count}")

# Show high confidence tasks
high_conf_tasks = [t for t in tasks if t['confidence'] >= 0.8]
print(f"\n🎯 High Confidence Tasks ({len(high_conf_tasks)}/{len(tasks)}):")
for i, task in enumerate(high_conf_tasks[:5], 1):
    print(f"\n{i}. {task['description'][:70]}...")
    print(f"   Confidence: {task['confidence']:.0%} | Priority: {task['priority']} | Assignee: {task['assignee']}")

# Show urgent tasks
urgent_tasks = [t for t in tasks if t.get('urgency') in ['critical', 'high']]
if urgent_tasks:
    print(f"\n⚠️  Urgent Tasks ({len(urgent_tasks)}):")
    for i, task in enumerate(urgent_tasks, 1):
        print(f"\n{i}. [{task['urgency'].upper()}] {task['description'][:70]}...")
        print(f"   Due: {task.get('due_date_formatted', 'Not specified')}")

print("\n" + "="*80)
print("✅ Enhanced extraction complete! Check outputs/action_items/action_items_enhanced.md")
print("="*80)
