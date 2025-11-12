# Action Item Extraction - Evaluation Report

**Evaluation Date:** 2025-11-12T20:30:25.437748
**LLM Enabled:** True
**Total Meetings:** 10

## Overall Performance

### Key Metrics (Academic Standard)

| Metric | Value | Description |
|--------|-------|-------------|
| **Precision** | 74.42% | Proportion of extracted tasks that are correct (TP / (TP + FP)) |
| **Recall** | 96.57% | Proportion of ground truth tasks found (TP / (TP + FN)) |
| **F1 Score** | 83.37% | Harmonic mean of precision and recall |
| **Match Quality** | 90.91% | Average semantic similarity of matched tasks |

### Confusion Matrix

| | Predicted Positive | Predicted Negative |
|---|---|---|
| **Actual Positive** | TP = 53 | FN = 2 |
| **Actual Negative** | FP = 24 | TN = N/A |

### Entity-Level Accuracy

| Entity Type | Exact Match | Partial Match | Notes |
|-------------|-------------|---------------|-------|
| **Assignee** | 66.42% | 80.50% | Person extraction accuracy |
| **Deadline** | 90.24% | N/A | Date extraction rate |

### Task Counts

- **Ground Truth Tasks:** 55
- **Extracted Tasks:** 77
- **Successfully Matched:** 53
- **False Positives:** 24
- **False Negatives:** 2

### Quality Distribution

- **Excellent:** 6 meetings (60.0%)
- **Good:** 4 meetings (40.0%)

## Performance Analysis

✅ **High Recall**: The system finds most ground truth tasks effectively.


## Detailed Results by Meeting

| Meeting | Type | F1 | Precision | Recall | Quality | GT/Ext/Match |
|---------|------|----|-----------| -------|---------|-------------|
| meeting_000.json | Sprint Planning | 0.76 | 0.62 | 1.00 | Good | 8/13/8 |
| meeting_001.json | Daily Standup | 1.00 | 1.00 | 1.00 | Excellent | 4/4/4 |
| meeting_002.json | Product Review | 0.73 | 0.57 | 1.00 | Good | 8/14/8 |
| meeting_003.json | Engineering Syn | 0.86 | 0.75 | 1.00 | Excellent | 3/4/3 |
| meeting_004.json | Marketing Campa | 0.91 | 0.83 | 1.00 | Excellent | 5/6/5 |
| meeting_005.json | Sales Strategy | 0.71 | 0.60 | 0.86 | Good | 7/10/6 |
| meeting_006.json | Design Review | 0.67 | 0.57 | 0.80 | Good | 5/7/4 |
| meeting_007.json | Budget Planning | 0.80 | 0.67 | 1.00 | Excellent | 6/9/6 |
| meeting_008.json | Retrospective | 1.00 | 1.00 | 1.00 | Excellent | 4/4/4 |
| meeting_009.json | Client Kickoff | 0.91 | 0.83 | 1.00 | Excellent | 5/6/5 |

---

*This report uses standard academic metrics for information extraction evaluation.*
