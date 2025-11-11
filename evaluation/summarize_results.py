"""
Quick summary script to display evaluation results in a nice format.
"""

import json
from pathlib import Path
from typing import Dict, Any


def print_banner(text: str):
    """Print a nice banner."""
    width = 70
    print("\n" + "=" * width)
    print(f" {text.center(width - 2)} ")
    print("=" * width + "\n")


def print_metric_bar(name: str, value: float, width: int = 50):
    """Print a metric with a visual bar."""
    filled = int(value * width)
    bar = "█" * filled + "░" * (width - filled)
    percentage = f"{value:.1%}"
    print(f"  {name:.<25} {bar} {percentage:>7}")


def print_quality_distribution(dist: Dict[str, int]):
    """Print quality distribution with visual bars."""
    total = sum(dist.values())
    max_count = max(dist.values())
    
    quality_order = ["Excellent", "Good", "Fair", "Poor", "Very Poor"]
    
    for quality in quality_order:
        if quality not in dist:
            continue
        
        count = dist[quality]
        percentage = count / total
        bar_width = int((count / max_count) * 40)
        bar = "▓" * bar_width
        
        emoji = {
            "Excellent": "🌟",
            "Good": "✅",
            "Fair": "⚠️",
            "Poor": "❌",
            "Very Poor": "🔴"
        }.get(quality, "•")
        
        print(f"  {emoji} {quality:.<20} {bar:<40} {count:>3} ({percentage:.1%})")


def summarize_evaluation(test_data_dir: Path = None):
    """Print a beautiful summary of evaluation results."""
    if test_data_dir is None:
        test_data_dir = Path("evaluation/test_data_50")
    
    # Load dataset summary
    dataset_file = test_data_dir / "dataset_summary.json"
    if dataset_file.exists():
        with open(dataset_file, 'r') as f:
            dataset = json.load(f)
    else:
        dataset = None
    
    # Check for evaluation report
    report_file = test_data_dir / "evaluation_report_no_llm.md"
    if not report_file.exists():
        print(f"❌ No evaluation report found at {report_file}")
        print("   Run: python evaluation/action_item_evaluator.py evaluation/test_data_50")
        return
    
    # Parse key metrics from report (simple parsing)
    with open(report_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract metrics
    metrics = {}
    for line in content.split('\n'):
        if '**Precision:**' in line:
            metrics['precision'] = float(line.split('**Precision:**')[1].strip().replace('%', '')) / 100
        elif '**Recall:**' in line:
            metrics['recall'] = float(line.split('**Recall:**')[1].strip().replace('%', '')) / 100
        elif '**F1 Score:**' in line:
            metrics['f1'] = float(line.split('**F1 Score:**')[1].strip().replace('%', '')) / 100
        elif '**Average Match Score:**' in line:
            metrics['match'] = float(line.split('**Average Match Score:**')[1].strip().replace('%', '')) / 100
        elif '**Ground Truth Tasks:**' in line:
            metrics['gt_tasks'] = int(line.split('**Ground Truth Tasks:**')[1].strip())
        elif '**Extracted Tasks:**' in line:
            metrics['ext_tasks'] = int(line.split('**Extracted Tasks:**')[1].strip())
        elif '**Successfully Matched:**' in line:
            metrics['matched'] = int(line.split('**Successfully Matched:**')[1].strip())
    
    # Extract quality distribution
    quality_dist = {}
    in_quality_section = False
    for line in content.split('\n'):
        if '### Quality Distribution' in line:
            in_quality_section = True
            continue
        if in_quality_section and line.startswith('- **'):
            parts = line.split(':**')
            if len(parts) == 2:
                quality = parts[0].replace('- **', '').strip()
                count = int(parts[1].split('meetings')[0].strip())
                quality_dist[quality] = count
        elif in_quality_section and line.startswith('##'):
            break
    
    # Print beautiful summary
    print_banner("ACTION ITEM EXTRACTION - EVALUATION SUMMARY")
    
    if dataset:
        print("📊 DATASET STATISTICS")
        print(f"  • Total Transcripts: {dataset.get('total_transcripts', 'N/A')}")
        print(f"  • Total Tasks: {dataset.get('total_tasks', 'N/A')}")
        print(f"  • Tasks with Assignees: {dataset.get('tasks_with_assignees', 'N/A')}")
        print(f"  • Tasks with Deadlines: {dataset.get('tasks_with_deadlines', 'N/A')}")
        
        if 'pattern_types' in dataset:
            print(f"\n  Pattern Distribution:")
            for pattern, count in dataset['pattern_types'].items():
                print(f"    - {pattern}: {count}")
        print()
    
    print("🎯 PERFORMANCE METRICS")
    print()
    print_metric_bar("F1 Score", metrics.get('f1', 0))
    print_metric_bar("Precision", metrics.get('precision', 0))
    print_metric_bar("Recall", metrics.get('recall', 0))
    print_metric_bar("Match Quality", metrics.get('match', 0))
    print()
    
    print("📈 TASK EXTRACTION RESULTS")
    print(f"  • Ground Truth Tasks: {metrics.get('gt_tasks', 0)}")
    print(f"  • Extracted Tasks: {metrics.get('ext_tasks', 0)}")
    print(f"  • Successfully Matched: {metrics.get('matched', 0)}")
    
    if metrics.get('gt_tasks', 0) > 0:
        recall_pct = (metrics.get('matched', 0) / metrics.get('gt_tasks', 1)) * 100
        print(f"  • Recall Rate: {recall_pct:.1f}% of all tasks found!")
    print()
    
    print("🏆 QUALITY DISTRIBUTION")
    print()
    print_quality_distribution(quality_dist)
    print()
    
    # Overall assessment
    f1 = metrics.get('f1', 0)
    print("💡 ASSESSMENT")
    if f1 >= 0.80:
        print("  ✅ EXCELLENT performance! System is production-ready.")
    elif f1 >= 0.65:
        print("  ✅ GOOD performance! System works well for most cases.")
    elif f1 >= 0.50:
        print("  ⚠️  FAIR performance. Consider improvements.")
    else:
        print("  ❌ POOR performance. Needs significant work.")
    
    print(f"\n  F1 Score: {f1:.1%}")
    
    # Recommendations
    print("\n💭 RECOMMENDATIONS")
    
    precision = metrics.get('precision', 0)
    recall = metrics.get('recall', 0)
    
    if precision < 0.6:
        print("  ⚠️  Low precision - System extracts too many false positives")
        print("     → Consider increasing confidence threshold")
        print("     → Add stricter filtering for task patterns")
    
    if recall < 0.7:
        print("  ⚠️  Low recall - System misses some tasks")
        print("     → Expand task pattern library")
        print("     → Consider enabling LLM fallback")
    
    if precision >= 0.6 and recall >= 0.7:
        print("  ✅ Good balance between precision and recall!")
    
    print("\n" + "=" * 70 + "\n")
    print(f"📄 Full report: {report_file}")
    print()


if __name__ == "__main__":
    summarize_evaluation()
