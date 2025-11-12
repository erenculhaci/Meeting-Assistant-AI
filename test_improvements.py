"""Test improved date parsing and assignee extraction"""

from action_item_extraction.utils.date_parser import DateParser
from action_item_extraction.utils.person_extractor import PersonExtractor
from datetime import datetime

print("="*80)
print("DATE PARSER IMPROVEMENTS TEST")
print("="*80)

parser = DateParser(reference_date=datetime(2025, 11, 12))

test_phrases = [
    'within 48 hours',
    'early next week',
    'mid-week',
    'late this week',
    'first thing tomorrow',
    'before lunch',
    'after lunch',
    'no later than Friday',
    'immediately',
    'COB today',
    'start of next month',
    'by month end',
    'day after tomorrow',
    'in 3 hours',
    'within 2 weeks',
    'end of year',
    'start of week',
    'urgently'
]

for phrase in test_phrases:
    dates = parser.extract_dates(phrase)
    if dates:
        result = f"{dates[0][1].strftime('%Y-%m-%d %H:%M')}"
    else:
        result = "NOT FOUND"
    print(f"{phrase:30} -> {result}")

print("\n" + "="*80)
print("ASSIGNEE EXTRACTOR IMPROVEMENTS TEST")
print("="*80)

extractor = PersonExtractor()

test_sentences = [
    "Sarah and Tom, you both will handle this",
    "Let's have Mike and Jessica work on the API",
    "I want David to review the code",
    "Sarah's responsibility is to coordinate",
    "Assign this to Emily and Michael",
    "I'll handle the deployment myself",
    "Have Alex take care of the documentation",
    "Tom & Sarah should collaborate on this",
    "Maya is responsible for the testing",
    "We'll work on this together"
]

for sentence in test_sentences:
    assignees = extractor.extract_assignee_from_text(sentence)
    print(f"{sentence:50} -> {assignees}")
