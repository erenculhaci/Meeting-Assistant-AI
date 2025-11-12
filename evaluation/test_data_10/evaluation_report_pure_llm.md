# Action Item Extraction - Evaluation Report

**Evaluation Date:** 2025-11-12T21:38:22.948781
**LLM Enabled:** False
**Total Meetings:** 10

## Overall Performance

### Key Metrics (Academic Standard)

| Metric | Value | Description |
|--------|-------|-------------|
| **Precision** | 100.00% | Proportion of extracted tasks that are correct (TP / (TP + FP)) |
| **Recall** | 90.14% | Proportion of ground truth tasks found (TP / (TP + FN)) |
| **F1 Score** | 94.37% | Harmonic mean of precision and recall |
| **Match Quality** | 100.00% | Average semantic similarity of matched tasks |

### Confusion Matrix

| | Predicted Positive | Predicted Negative |
|---|---|---|
| **Actual Positive** | TP = 49 | FN = 6 |
| **Actual Negative** | FP = 0 | TN = N/A |

### Entity-Level Accuracy

| Entity Type | Exact Match | Partial Match | Notes |
|-------------|-------------|---------------|-------|
| **Assignee** | 97.50% | 97.50% | Person extraction accuracy |
| **Deadline** | 86.67% | N/A | Date extraction rate |

### Task Counts

- **Ground Truth Tasks:** 55
- **Extracted Tasks:** 49
- **Successfully Matched:** 49
- **False Positives:** 0
- **False Negatives:** 6

### Quality Distribution

- **Excellent:** 10 meetings (100.0%)

## Performance Analysis

✅ **High Precision**: The system has few false positives. Extracted tasks are highly reliable.

✅ **High Recall**: The system finds most ground truth tasks effectively.


## Detailed Results by Meeting

| Meeting | Type | F1 | Precision | Recall | Quality | GT/Ext/Match |
|---------|------|----|-----------| -------|---------|-------------|
| meeting_000.json | Sprint Planning | 1.00 | 1.00 | 1.00 | Excellent | 8/8/8 |
| meeting_001.json | Daily Standup | 1.00 | 1.00 | 1.00 | Excellent | 4/4/4 |
| meeting_002.json | Product Review | 0.86 | 1.00 | 0.75 | Excellent | 8/6/6 |
| meeting_003.json | Engineering Syn | 1.00 | 1.00 | 1.00 | Excellent | 3/3/3 |
| meeting_004.json | Marketing Campa | 1.00 | 1.00 | 1.00 | Excellent | 5/5/5 |
| meeting_005.json | Sales Strategy | 0.83 | 1.00 | 0.71 | Excellent | 7/5/5 |
| meeting_006.json | Design Review | 1.00 | 1.00 | 1.00 | Excellent | 5/5/5 |
| meeting_007.json | Budget Planning | 1.00 | 1.00 | 1.00 | Excellent | 6/6/6 |
| meeting_008.json | Retrospective | 0.86 | 1.00 | 0.75 | Excellent | 4/3/3 |
| meeting_009.json | Client Kickoff | 0.89 | 1.00 | 0.80 | Excellent | 5/4/4 |

---

*This report uses standard academic metrics for information extraction evaluation.*
