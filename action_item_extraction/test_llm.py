"""
Test enhanced action item extraction WITH LLM fallback.
Requires OPENAI_API_KEY in .env file.
"""

import sys
import os
from datetime import datetime

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Load environment variables from .env file
from action_item_extraction.load_env import load_env_file
load_env_file()

from action_item_extraction.extractor import extract_action_items

print("="*80)
print("ENHANCED ACTION ITEM EXTRACTION TEST - WITH LLM FALLBACK")
print("="*80)

# Check if OpenAI API key is set
if not os.getenv("OPENAI_API_KEY"):
    print("\n⚠️  WARNING: OPENAI_API_KEY not set!")
    print("LLM fallback will be disabled.")
    print("To enable it, set your API key:")
    print('  export OPENAI_API_KEY="your-key-here"  # Linux/Mac')
    print('  $env:OPENAI_API_KEY="your-key-here"   # PowerShell')
    use_llm = False
else:
    print("\n✅ OpenAI API key detected")
    use_llm = True

print("\nTesting with features:")
print("- Expanded task patterns (45+ patterns)")
print("- Urgency detection")
print("- Confidence scoring model")
print("- Semantic deduplication")
print("- Advanced date parsing")
print(f"- LLM fallback: {'✅ ENABLED' if use_llm else '❌ DISABLED'}")
print("="*80)

# Use absolute path
input_file = os.path.join(project_root, "outputs", "transcription", "transcript2.json")
output_file = os.path.join(project_root, "outputs", "action_items", "action_items_llm.md")

# Test with LLM fallback
tasks = extract_action_items(
    transcript_file_path=input_file,
    output_file=output_file,
    output_format="md",
    reference_date=datetime(2025, 11, 1),
    use_llm_fallback=use_llm,
    llm_model="gpt-4o-mini"  # Cost-efficient model
)

print(f"\n✅ Extracted {len(tasks)} tasks")

# Show statistics
urgency_counts = {}
priority_counts = {}
status_counts = {}
llm_clarified = 0

for task in tasks:
    urgency = task.get('urgency', 'normal')
    urgency_counts[urgency] = urgency_counts.get(urgency, 0) + 1
    
    priority = task.get('priority', 'medium')
    priority_counts[priority] = priority_counts.get(priority, 0) + 1
    
    status = task.get('status', 'pending')
    status_counts[status] = status_counts.get(status, 0) + 1
    
    if task.get('llm_clarified'):
        llm_clarified += 1

print("\n📊 Task Statistics:")
print("\nBy Urgency:")
for urgency, count in sorted(urgency_counts.items()):
    print(f"  - {urgency.capitalize()}: {count}")

print("\nBy Priority:")
for priority, count in sorted(priority_counts.items()):
    print(f"  - {priority.capitalize()}: {count}")

print("\nBy Status:")
for status, count in sorted(status_counts.items()):
    print(f"  - {status.capitalize()}: {count}")

if use_llm:
    print(f"\n🤖 LLM Clarified: {llm_clarified}/{len(tasks)} tasks")

# Show high confidence tasks
high_conf = [t for t in tasks if t.get('confidence', 0) >= 0.8]
print(f"\n🎯 High Confidence Tasks ({len(high_conf)}/{len(tasks)}):\n")

for i, task in enumerate(high_conf[:5], 1):  # Show top 5
    desc = task['description'][:60] + "..." if len(task['description']) > 60 else task['description']
    assignee = task.get('assignee', 'Unassigned')
    priority = task.get('priority', 'medium')
    confidence = int(task.get('confidence', 0) * 100)
    llm_mark = " 🤖" if task.get('llm_clarified') else ""
    
    print(f"{i}. {desc}")
    print(f"   Confidence: {confidence}% | Priority: {priority} | Assignee: {assignee}{llm_mark}")
    
    if task.get('llm_reasoning'):
        print(f"   LLM: {task['llm_reasoning'][:70]}...")
    print()

# Show tasks with invalid assignees that need LLM help
invalid_assignees = ['that', 'this', 'yes', 'no', 'alright', 'okay']
problematic = [t for t in tasks if t.get('assignee', '').lower() in invalid_assignees]

if problematic and not use_llm:
    print(f"\n⚠️  Found {len(problematic)} tasks with invalid assignees:")
    for task in problematic[:3]:
        print(f"   - '{task['description'][:50]}...' → Assignee: {task['assignee']}")
    print("\n   💡 Enable LLM fallback to fix these automatically!")

print("\n" + "="*80)
print(f"✅ Enhanced extraction complete! Check {output_file}")
print("="*80)
