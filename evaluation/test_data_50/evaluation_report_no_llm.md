# Action Item Extraction - Evaluation Report

**Evaluation Date:** 2025-11-11T23:45:42.521777
**LLM Enabled:** False
**Total Meetings:** 50

## Overall Performance

### Key Metrics

- **Precision:** 54.35%
- **Recall:** 100.00%
- **F1 Score:** 70.02%
- **Average Match Score:** 90.00%

### Assignee Accuracy

- **Exact Match:** 15.13%
- **Partial Match:** 27.70%

### Deadline Accuracy

- **Extraction Rate:** 51.48%

### Task Counts

- **Ground Truth Tasks:** 284
- **Extracted Tasks:** 527
- **Successfully Matched:** 284

### Quality Distribution

- **Excellent:** 6 meetings
- **Fair:** 11 meetings
- **Good:** 33 meetings

## Detailed Results

### meeting_000.json (Sprint Planning)

- **F1 Score:** 54.55%
- **Quality:** Fair
- **Tasks:** 3 GT / 8 Extracted / 3 Matched
- **Strengths:** High recall - finds most tasks
- **Weaknesses:** Low precision - many false positives, Poor assignee extraction

### meeting_001.json (Daily Standup)

- **F1 Score:** 66.67%
- **Quality:** Good
- **Tasks:** 6 GT / 12 Extracted / 6 Matched
- **Strengths:** High recall - finds most tasks
- **Weaknesses:** Poor assignee extraction

### meeting_002.json (Product Review)

- **F1 Score:** 70.59%
- **Quality:** Good
- **Tasks:** 6 GT / 11 Extracted / 6 Matched
- **Strengths:** High recall - finds most tasks, Good deadline extraction

### meeting_003.json (Engineering Sync)

- **F1 Score:** 80.00%
- **Quality:** Excellent
- **Tasks:** 4 GT / 6 Extracted / 4 Matched
- **Strengths:** High recall - finds most tasks
- **Weaknesses:** Poor assignee extraction, Poor deadline extraction

### meeting_004.json (Marketing Campaign)

- **F1 Score:** 75.00%
- **Quality:** Good
- **Tasks:** 3 GT / 5 Extracted / 3 Matched
- **Strengths:** High recall - finds most tasks, Good deadline extraction
- **Weaknesses:** Poor assignee extraction

### meeting_005.json (Sales Strategy)

- **F1 Score:** 66.67%
- **Quality:** Good
- **Tasks:** 3 GT / 6 Extracted / 3 Matched
- **Strengths:** High recall - finds most tasks
- **Weaknesses:** Poor assignee extraction, Poor deadline extraction

### meeting_006.json (Design Review)

- **F1 Score:** 76.92%
- **Quality:** Good
- **Tasks:** 5 GT / 8 Extracted / 5 Matched
- **Strengths:** High recall - finds most tasks
- **Weaknesses:** Poor assignee extraction

### meeting_007.json (Budget Planning)

- **F1 Score:** 70.00%
- **Quality:** Good
- **Tasks:** 7 GT / 13 Extracted / 7 Matched
- **Strengths:** High recall - finds most tasks
- **Weaknesses:** Poor assignee extraction, Poor deadline extraction

### meeting_008.json (Retrospective)

- **F1 Score:** 80.00%
- **Quality:** Excellent
- **Tasks:** 4 GT / 6 Extracted / 4 Matched
- **Strengths:** High recall - finds most tasks
- **Weaknesses:** Poor assignee extraction

### meeting_009.json (Client Kickoff)

- **F1 Score:** 66.67%
- **Quality:** Good
- **Tasks:** 5 GT / 10 Extracted / 5 Matched
- **Strengths:** High recall - finds most tasks, Good deadline extraction

### meeting_010.json (Security Audit)

- **F1 Score:** 70.59%
- **Quality:** Good
- **Tasks:** 6 GT / 11 Extracted / 6 Matched
- **Strengths:** High recall - finds most tasks
- **Weaknesses:** Poor assignee extraction, Poor deadline extraction

### meeting_011.json (Performance Review)

- **F1 Score:** 60.00%
- **Quality:** Fair
- **Tasks:** 3 GT / 7 Extracted / 3 Matched
- **Strengths:** High recall - finds most tasks, Good deadline extraction
- **Weaknesses:** Low precision - many false positives

### meeting_012.json (Launch Planning)

- **F1 Score:** 58.33%
- **Quality:** Fair
- **Tasks:** 7 GT / 17 Extracted / 7 Matched
- **Strengths:** High recall - finds most tasks
- **Weaknesses:** Low precision - many false positives, Poor assignee extraction, Poor deadline extraction

### meeting_013.json (Architecture Discussion)

- **F1 Score:** 70.59%
- **Quality:** Good
- **Tasks:** 6 GT / 11 Extracted / 6 Matched
- **Strengths:** High recall - finds most tasks
- **Weaknesses:** Poor assignee extraction

### meeting_014.json (User Research)

- **F1 Score:** 62.50%
- **Quality:** Fair
- **Tasks:** 5 GT / 11 Extracted / 5 Matched
- **Strengths:** High recall - finds most tasks, Good deadline extraction
- **Weaknesses:** Low precision - many false positives

### meeting_015.json (Crisis Management)

- **F1 Score:** 66.67%
- **Quality:** Good
- **Tasks:** 3 GT / 6 Extracted / 3 Matched
- **Strengths:** High recall - finds most tasks
- **Weaknesses:** Poor assignee extraction

### meeting_016.json (Quarterly Planning)

- **F1 Score:** 72.73%
- **Quality:** Good
- **Tasks:** 8 GT / 14 Extracted / 8 Matched
- **Strengths:** High recall - finds most tasks
- **Weaknesses:** Poor assignee extraction

### meeting_017.json (Team Building)

- **F1 Score:** 60.00%
- **Quality:** Fair
- **Tasks:** 3 GT / 7 Extracted / 3 Matched
- **Strengths:** High recall - finds most tasks
- **Weaknesses:** Low precision - many false positives, Poor assignee extraction

### meeting_018.json (Technical Debt)

- **F1 Score:** 75.00%
- **Quality:** Good
- **Tasks:** 3 GT / 5 Extracted / 3 Matched
- **Strengths:** High recall - finds most tasks
- **Weaknesses:** Poor deadline extraction

### meeting_019.json (API Design)

- **F1 Score:** 66.67%
- **Quality:** Good
- **Tasks:** 5 GT / 10 Extracted / 5 Matched
- **Strengths:** High recall - finds most tasks
- **Weaknesses:** Poor assignee extraction, Poor deadline extraction

### meeting_020.json (Data Migration)

- **F1 Score:** 75.00%
- **Quality:** Good
- **Tasks:** 6 GT / 10 Extracted / 6 Matched
- **Strengths:** High recall - finds most tasks
- **Weaknesses:** Poor assignee extraction, Poor deadline extraction

### meeting_021.json (Compliance Review)

- **F1 Score:** 66.67%
- **Quality:** Good
- **Tasks:** 7 GT / 14 Extracted / 7 Matched
- **Strengths:** High recall - finds most tasks, Good deadline extraction
- **Weaknesses:** Poor assignee extraction

### meeting_022.json (Customer Feedback)

- **F1 Score:** 70.59%
- **Quality:** Good
- **Tasks:** 6 GT / 11 Extracted / 6 Matched
- **Strengths:** High recall - finds most tasks, Good deadline extraction

### meeting_023.json (Partnership Discussion)

- **F1 Score:** 76.92%
- **Quality:** Good
- **Tasks:** 5 GT / 8 Extracted / 5 Matched
- **Strengths:** High recall - finds most tasks
- **Weaknesses:** Poor assignee extraction

### meeting_024.json (Vendor Selection)

- **F1 Score:** 69.57%
- **Quality:** Good
- **Tasks:** 8 GT / 15 Extracted / 8 Matched
- **Strengths:** High recall - finds most tasks
- **Weaknesses:** Poor assignee extraction, Poor deadline extraction

### meeting_025.json (Infrastructure Planning)

- **F1 Score:** 66.67%
- **Quality:** Good
- **Tasks:** 8 GT / 16 Extracted / 8 Matched
- **Strengths:** High recall - finds most tasks, Good deadline extraction
- **Weaknesses:** Poor assignee extraction

### meeting_026.json (Training Session)

- **F1 Score:** 88.89%
- **Quality:** Excellent
- **Tasks:** 8 GT / 10 Extracted / 8 Matched
- **Strengths:** High precision - few false positives, High recall - finds most tasks
- **Weaknesses:** Poor assignee extraction

### meeting_027.json (Beta Launch)

- **F1 Score:** 73.68%
- **Quality:** Good
- **Tasks:** 7 GT / 12 Extracted / 7 Matched
- **Strengths:** High recall - finds most tasks
- **Weaknesses:** Poor assignee extraction, Poor deadline extraction

### meeting_028.json (Feature Prioritization)

- **F1 Score:** 82.35%
- **Quality:** Excellent
- **Tasks:** 7 GT / 10 Extracted / 7 Matched
- **Strengths:** High recall - finds most tasks
- **Weaknesses:** Poor assignee extraction, Poor deadline extraction

### meeting_029.json (Bug Triage)

- **F1 Score:** 58.82%
- **Quality:** Fair
- **Tasks:** 5 GT / 12 Extracted / 5 Matched
- **Strengths:** High recall - finds most tasks
- **Weaknesses:** Low precision - many false positives, Poor assignee extraction

### meeting_030.json (Documentation Review)

- **F1 Score:** 66.67%
- **Quality:** Good
- **Tasks:** 5 GT / 10 Extracted / 5 Matched
- **Strengths:** High recall - finds most tasks, Good deadline extraction
- **Weaknesses:** Poor assignee extraction

### meeting_031.json (Release Planning)

- **F1 Score:** 82.35%
- **Quality:** Excellent
- **Tasks:** 7 GT / 10 Extracted / 7 Matched
- **Strengths:** High recall - finds most tasks
- **Weaknesses:** Poor assignee extraction, Poor deadline extraction

### meeting_032.json (Sprint Planning)

- **F1 Score:** 72.73%
- **Quality:** Good
- **Tasks:** 4 GT / 7 Extracted / 4 Matched
- **Strengths:** High recall - finds most tasks
- **Weaknesses:** Poor assignee extraction, Poor deadline extraction

### meeting_033.json (Daily Standup)

- **F1 Score:** 73.68%
- **Quality:** Good
- **Tasks:** 7 GT / 12 Extracted / 7 Matched
- **Strengths:** High recall - finds most tasks
- **Weaknesses:** Poor assignee extraction, Poor deadline extraction

### meeting_034.json (Product Review)

- **F1 Score:** 70.59%
- **Quality:** Good
- **Tasks:** 6 GT / 11 Extracted / 6 Matched
- **Strengths:** High recall - finds most tasks
- **Weaknesses:** Poor assignee extraction

### meeting_035.json (Engineering Sync)

- **F1 Score:** 66.67%
- **Quality:** Good
- **Tasks:** 7 GT / 14 Extracted / 7 Matched
- **Strengths:** High recall - finds most tasks
- **Weaknesses:** Poor assignee extraction

### meeting_036.json (Marketing Campaign)

- **F1 Score:** 57.14%
- **Quality:** Fair
- **Tasks:** 4 GT / 10 Extracted / 4 Matched
- **Strengths:** High recall - finds most tasks
- **Weaknesses:** Low precision - many false positives, Poor assignee extraction, Poor deadline extraction

### meeting_037.json (Sales Strategy)

- **F1 Score:** 80.00%
- **Quality:** Excellent
- **Tasks:** 6 GT / 9 Extracted / 6 Matched
- **Strengths:** High recall - finds most tasks
- **Weaknesses:** Poor assignee extraction, Poor deadline extraction

### meeting_038.json (Design Review)

- **F1 Score:** 76.19%
- **Quality:** Good
- **Tasks:** 8 GT / 13 Extracted / 8 Matched
- **Strengths:** High recall - finds most tasks
- **Weaknesses:** Poor assignee extraction, Poor deadline extraction

### meeting_039.json (Budget Planning)

- **F1 Score:** 73.68%
- **Quality:** Good
- **Tasks:** 7 GT / 12 Extracted / 7 Matched
- **Strengths:** High recall - finds most tasks

### meeting_040.json (Retrospective)

- **F1 Score:** 73.68%
- **Quality:** Good
- **Tasks:** 7 GT / 12 Extracted / 7 Matched
- **Strengths:** High recall - finds most tasks
- **Weaknesses:** Poor assignee extraction, Poor deadline extraction

### meeting_041.json (Client Kickoff)

- **F1 Score:** 63.16%
- **Quality:** Fair
- **Tasks:** 6 GT / 13 Extracted / 6 Matched
- **Strengths:** High recall - finds most tasks, Good deadline extraction
- **Weaknesses:** Low precision - many false positives, Poor assignee extraction

### meeting_042.json (Security Audit)

- **F1 Score:** 72.73%
- **Quality:** Good
- **Tasks:** 8 GT / 14 Extracted / 8 Matched
- **Strengths:** High recall - finds most tasks, Good deadline extraction
- **Weaknesses:** Poor assignee extraction

### meeting_043.json (Performance Review)

- **F1 Score:** 62.50%
- **Quality:** Fair
- **Tasks:** 5 GT / 11 Extracted / 5 Matched
- **Strengths:** High recall - finds most tasks, Good deadline extraction
- **Weaknesses:** Low precision - many false positives, Poor assignee extraction

### meeting_044.json (Launch Planning)

- **F1 Score:** 58.82%
- **Quality:** Fair
- **Tasks:** 5 GT / 12 Extracted / 5 Matched
- **Strengths:** High recall - finds most tasks, Good deadline extraction
- **Weaknesses:** Low precision - many false positives, Poor assignee extraction

### meeting_045.json (Architecture Discussion)

- **F1 Score:** 77.78%
- **Quality:** Good
- **Tasks:** 7 GT / 11 Extracted / 7 Matched
- **Strengths:** High recall - finds most tasks, Good deadline extraction
- **Weaknesses:** Poor assignee extraction

### meeting_046.json (User Research)

- **F1 Score:** 70.59%
- **Quality:** Good
- **Tasks:** 6 GT / 11 Extracted / 6 Matched
- **Strengths:** High recall - finds most tasks
- **Weaknesses:** Poor assignee extraction

### meeting_047.json (Crisis Management)

- **F1 Score:** 63.16%
- **Quality:** Fair
- **Tasks:** 6 GT / 13 Extracted / 6 Matched
- **Strengths:** High recall - finds most tasks
- **Weaknesses:** Low precision - many false positives, Poor assignee extraction

### meeting_048.json (Quarterly Planning)

- **F1 Score:** 66.67%
- **Quality:** Good
- **Tasks:** 3 GT / 6 Extracted / 3 Matched
- **Strengths:** High recall - finds most tasks
- **Weaknesses:** Poor assignee extraction, Poor deadline extraction

### meeting_049.json (Team Building)

- **F1 Score:** 72.73%
- **Quality:** Good
- **Tasks:** 8 GT / 14 Extracted / 8 Matched
- **Strengths:** High recall - finds most tasks
- **Weaknesses:** Poor assignee extraction

