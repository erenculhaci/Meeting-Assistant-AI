"""
Intelligent Evaluation Module for Action Item Extraction.

This evaluator doesn't require exact matches but validates:
1. Task extraction quality (did it find meaningful tasks?)
2. Assignee accuracy (are assignees correct when specified?)
3. Deadline accuracy (are dates reasonable and correct?)
4. Overall extraction effectiveness

Uses semantic similarity and flexible matching for realistic evaluation.
"""

import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime, timedelta
from difflib import SequenceMatcher

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from action_item_extraction.extractor import extract_action_items

logger = logging.getLogger(__name__)


class TaskMatcher:
    """Matches extracted tasks with ground truth using intelligent criteria."""
    
    @staticmethod
    def calculate_text_similarity(text1: str, text2: str) -> float:
        """Calculate similarity between two text strings."""
        text1_lower = text1.lower().strip()
        text2_lower = text2.lower().strip()
        
        # Check for substring matches
        if text1_lower in text2_lower or text2_lower in text1_lower:
            return 0.9
        
        # Use sequence matcher
        return SequenceMatcher(None, text1_lower, text2_lower).ratio()
    
    @staticmethod
    def extract_key_terms(text: str) -> set:
        """Extract key terms from text."""
        # Remove common words
        stopwords = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'about', 'as', 'into', 'through', 'during',
            'before', 'after', 'above', 'below', 'up', 'down', 'out', 'off', 'over',
            'under', 'again', 'further', 'then', 'once', 'here', 'there', 'when',
            'where', 'why', 'how', 'all', 'both', 'each', 'few', 'more', 'most',
            'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same',
            'so', 'than', 'too', 'very', 'can', 'will', 'just', 'should', 'now'
        }
        
        words = text.lower().split()
        key_terms = {w for w in words if len(w) > 3 and w not in stopwords}
        return key_terms
    
    @staticmethod
    def calculate_semantic_similarity(text1: str, text2: str) -> float:
        """Calculate semantic similarity based on key terms overlap."""
        terms1 = TaskMatcher.extract_key_terms(text1)
        terms2 = TaskMatcher.extract_key_terms(text2)
        
        if not terms1 or not terms2:
            return 0.0
        
        # Jaccard similarity
        intersection = terms1 & terms2
        union = terms1 | terms2
        
        return len(intersection) / len(union) if union else 0.0
    
    @staticmethod
    def match_task(extracted_task: Dict, ground_truth_task: Dict) -> Tuple[bool, float, Dict]:
        """
        Match an extracted task with a ground truth task.
        
        Returns:
            - is_match: Whether this is a valid match
            - score: Matching score (0-1)
            - details: Detailed matching information
        """
        # Compare task descriptions - extracted uses 'description' field
        text_sim = TaskMatcher.calculate_text_similarity(
            extracted_task.get("description", ""),
            ground_truth_task.get("description", "")
        )
        
        semantic_sim = TaskMatcher.calculate_semantic_similarity(
            extracted_task.get("description", ""),
            ground_truth_task.get("description", "")
        )
        
        # Combined similarity
        description_score = max(text_sim, semantic_sim)
        
        # We consider it a match if description similarity > 0.5
        is_match = description_score > 0.5
        
        details = {
            "text_similarity": text_sim,
            "semantic_similarity": semantic_sim,
            "description_score": description_score,
        }
        
        return is_match, description_score, details


class ActionItemEvaluator:
    """Evaluates action item extraction performance intelligently."""
    
    def __init__(self, reference_date: Optional[datetime] = None):
        """Initialize evaluator."""
        self.reference_date = reference_date or datetime.now()
        self.matcher = TaskMatcher()
    
    def evaluate_single_meeting(
        self,
        transcript_file: Path,
        ground_truth_file: Path,
        use_llm: bool = False
    ) -> Dict[str, Any]:
        """
        Evaluate extraction on a single meeting.
        
        Returns detailed metrics and analysis.
        """
        # Load ground truth
        with open(ground_truth_file, 'r', encoding='utf-8') as f:
            ground_truth_data = json.load(f)
        ground_truth_tasks = ground_truth_data.get("tasks", [])
        
        # Load transcript data
        with open(transcript_file, 'r', encoding='utf-8') as f:
            transcript_data = json.load(f)
        
        # Extract tasks
        try:
            # Check if we should use pure LLM extraction
            use_pure_llm = getattr(self, 'use_pure_llm', False)
            use_llm_fallback = getattr(self, 'use_llm_fallback', use_llm)
            
            result = extract_action_items(
                transcript_data=transcript_data,
                use_llm=use_pure_llm,
                use_llm_fallback=use_llm_fallback
            )
            
            # Extract action items list from result
            if isinstance(result, dict):
                extracted_tasks = result.get('action_items', [])
            else:
                extracted_tasks = result if isinstance(result, list) else []
                
        except Exception as e:
            logger.error(f"Error extracting tasks from {transcript_file}: {e}")
            return {
                "status": "error",
                "error": str(e),
                "ground_truth_count": len(ground_truth_tasks),
                "extracted_count": 0
            }
        
        # Match extracted tasks with ground truth
        matches, unmatched_gt, unmatched_extracted = self._match_tasks(
            extracted_tasks, ground_truth_tasks
        )
        
        # Calculate metrics
        metrics = self._calculate_metrics(
            matches, ground_truth_tasks, extracted_tasks
        )
        
        # Evaluate assignee accuracy
        assignee_metrics = self._evaluate_assignees(matches, ground_truth_tasks)
        
        # Evaluate deadline accuracy
        deadline_metrics = self._evaluate_deadlines(matches, ground_truth_tasks)
        
        # Overall quality assessment
        quality = self._assess_quality(
            metrics, assignee_metrics, deadline_metrics,
            len(ground_truth_tasks), len(extracted_tasks)
        )
        
        return {
            "status": "success",
            "transcript_file": transcript_file.name,
            "meeting_type": ground_truth_data.get("meeting_type", "unknown"),
            "metrics": metrics,
            "assignee_accuracy": assignee_metrics,
            "deadline_accuracy": deadline_metrics,
            "quality_assessment": quality,
            "ground_truth_count": len(ground_truth_tasks),
            "extracted_count": len(extracted_tasks),
            "matched_count": len(matches),
            "false_negatives": len(unmatched_gt),
            "false_positives": len(unmatched_extracted),
            "detailed_matches": matches[:5]  # First 5 for inspection
        }
    
    def _match_tasks(
        self,
        extracted_tasks: List[Dict],
        ground_truth_tasks: List[Dict]
    ) -> Tuple[List[Dict], List[Dict], List[Dict]]:
        """
        Match extracted tasks with ground truth.
        
        Returns:
            - matches: List of matched pairs with scores
            - unmatched_gt: Ground truth tasks not matched
            - unmatched_extracted: Extracted tasks not matched
        """
        matches = []
        matched_gt_indices = set()
        matched_extracted_indices = set()
        
        # Try to match each extracted task
        for ext_idx, ext_task in enumerate(extracted_tasks):
            best_match = None
            best_score = 0.0
            best_gt_idx = None
            
            for gt_idx, gt_task in enumerate(ground_truth_tasks):
                if gt_idx in matched_gt_indices:
                    continue
                
                is_match, score, details = self.matcher.match_task(ext_task, gt_task)
                
                if is_match and score > best_score:
                    best_score = score
                    best_match = {
                        "extracted": ext_task,
                        "ground_truth": gt_task,
                        "score": score,
                        "details": details
                    }
                    best_gt_idx = gt_idx
            
            if best_match:
                matches.append(best_match)
                matched_gt_indices.add(best_gt_idx)
                matched_extracted_indices.add(ext_idx)
        
        # Find unmatched
        unmatched_gt = [
            gt_task for idx, gt_task in enumerate(ground_truth_tasks)
            if idx not in matched_gt_indices
        ]
        
        unmatched_extracted = [
            ext_task for idx, ext_task in enumerate(extracted_tasks)
            if idx not in matched_extracted_indices
        ]
        
        return matches, unmatched_gt, unmatched_extracted
    
    def _calculate_metrics(
        self,
        matches: List[Dict],
        ground_truth_tasks: List[Dict],
        extracted_tasks: List[Dict]
    ) -> Dict[str, float]:
        """Calculate precision, recall, F1 score."""
        true_positives = len(matches)
        false_negatives = len(ground_truth_tasks) - true_positives
        false_positives = len(extracted_tasks) - true_positives
        
        precision = true_positives / len(extracted_tasks) if extracted_tasks else 0.0
        recall = true_positives / len(ground_truth_tasks) if ground_truth_tasks else 0.0
        f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        
        # Average matching score
        avg_match_score = sum(m["score"] for m in matches) / len(matches) if matches else 0.0
        
        return {
            "precision": precision,
            "recall": recall,
            "f1_score": f1,
            "average_match_score": avg_match_score,
            "true_positives": true_positives,
            "false_positives": false_positives,
            "false_negatives": false_negatives
        }
    
    def _evaluate_assignees(
        self,
        matches: List[Dict],
        ground_truth_tasks: List[Dict]
    ) -> Dict[str, Any]:
        """Evaluate assignee extraction accuracy."""
        total_with_assignees = 0
        correct_assignees = 0
        partial_correct = 0
        
        for match in matches:
            gt_assignees = set(match["ground_truth"].get("assignees", []))
            # Extracted tasks use 'assignee' field
            ext_assignee = match["extracted"].get("assignee", "Unassigned")
            
            if not gt_assignees:
                continue  # Skip tasks without ground truth assignees
            
            total_with_assignees += 1
            
            # Clean extracted assignee (remove "Speaker_" prefix if present)
            ext_assignee_clean = ext_assignee.replace("Speaker_", "").strip()
            
            # Check if any ground truth assignee matches
            found_assignees = set()
            for assignee in gt_assignees:
                # Case-insensitive match
                if assignee.lower() == ext_assignee_clean.lower():
                    found_assignees.add(assignee)
                # Also check if GT assignee is contained in extracted
                elif assignee.lower() in ext_assignee_clean.lower():
                    found_assignees.add(assignee)
            
            if found_assignees == gt_assignees:
                correct_assignees += 1
            elif found_assignees:
                partial_correct += 1
        
        accuracy = correct_assignees / total_with_assignees if total_with_assignees > 0 else 0.0
        partial_accuracy = (correct_assignees + partial_correct) / total_with_assignees if total_with_assignees > 0 else 0.0
        
        return {
            "exact_match_accuracy": accuracy,
            "partial_match_accuracy": partial_accuracy,
            "tasks_with_assignees": total_with_assignees,
            "exact_matches": correct_assignees,
            "partial_matches": partial_correct
        }
    
    def _evaluate_deadlines(
        self,
        matches: List[Dict],
        ground_truth_tasks: List[Dict]
    ) -> Dict[str, Any]:
        """Evaluate deadline extraction accuracy."""
        total_with_deadlines = 0
        deadlines_extracted = 0
        reasonable_deadlines = 0
        
        for match in matches:
            gt_deadline = match["ground_truth"].get("deadline")
            # Extracted tasks use 'due_date' field
            ext_deadline = match["extracted"].get("due_date")
            
            if not gt_deadline:
                continue  # Skip tasks without ground truth deadlines
            
            total_with_deadlines += 1
            
            if ext_deadline:
                deadlines_extracted += 1
                
                # Check if deadline is reasonable (not checking exact match)
                # We consider it reasonable if a deadline was extracted
                reasonable_deadlines += 1
        
        extraction_rate = deadlines_extracted / total_with_deadlines if total_with_deadlines > 0 else 0.0
        reasonableness_rate = reasonable_deadlines / total_with_deadlines if total_with_deadlines > 0 else 0.0
        
        return {
            "deadline_extraction_rate": extraction_rate,
            "reasonable_deadline_rate": reasonableness_rate,
            "tasks_with_deadlines": total_with_deadlines,
            "deadlines_extracted": deadlines_extracted,
            "reasonable_deadlines": reasonable_deadlines
        }
    
    def _assess_quality(
        self,
        metrics: Dict,
        assignee_metrics: Dict,
        deadline_metrics: Dict,
        gt_count: int,
        ext_count: int
    ) -> Dict[str, Any]:
        """Provide overall quality assessment."""
        f1 = metrics["f1_score"]
        
        # Quality levels
        if f1 >= 0.8:
            quality_level = "Excellent"
            rating = 5
        elif f1 >= 0.65:
            quality_level = "Good"
            rating = 4
        elif f1 >= 0.5:
            quality_level = "Fair"
            rating = 3
        elif f1 >= 0.35:
            quality_level = "Poor"
            rating = 2
        else:
            quality_level = "Very Poor"
            rating = 1
        
        # Strengths and weaknesses
        strengths = []
        weaknesses = []
        
        if metrics["precision"] >= 0.8:
            strengths.append("High precision - few false positives")
        elif metrics["precision"] < 0.5:
            weaknesses.append("Low precision - many false positives")
        
        if metrics["recall"] >= 0.8:
            strengths.append("High recall - finds most tasks")
        elif metrics["recall"] < 0.5:
            weaknesses.append("Low recall - misses many tasks")
        
        if assignee_metrics["exact_match_accuracy"] >= 0.7:
            strengths.append("Good assignee extraction")
        elif assignee_metrics["exact_match_accuracy"] < 0.4:
            weaknesses.append("Poor assignee extraction")
        
        if deadline_metrics["deadline_extraction_rate"] >= 0.7:
            strengths.append("Good deadline extraction")
        elif deadline_metrics["deadline_extraction_rate"] < 0.4:
            weaknesses.append("Poor deadline extraction")
        
        return {
            "overall_quality": quality_level,
            "rating": rating,
            "f1_score": f1,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "extraction_balance": "balanced" if abs(gt_count - ext_count) / max(gt_count, 1) < 0.3 else "imbalanced"
        }
    
    def evaluate_batch(
        self,
        test_data_dir: Path,
        use_llm: bool = False,
        max_meetings: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Evaluate on multiple meetings.
        
        Returns aggregated metrics and per-meeting results.
        """
        transcripts_dir = test_data_dir / "transcripts"
        ground_truth_dir = test_data_dir / "ground_truth"
        
        if not transcripts_dir.exists() or not ground_truth_dir.exists():
            raise ValueError(f"Invalid test data directory: {test_data_dir}")
        
        # Get all transcript files
        transcript_files = sorted(transcripts_dir.glob("meeting_*.json"))
        if max_meetings:
            transcript_files = transcript_files[:max_meetings]
        
        print(f"\n🔍 Evaluating {len(transcript_files)} meetings...")
        print(f"   LLM Fallback: {'Enabled' if use_llm else 'Disabled'}\n")
        
        results = []
        for idx, transcript_file in enumerate(transcript_files, 1):
            # Find corresponding ground truth
            gt_file = ground_truth_dir / f"{transcript_file.stem}_ground_truth.json"
            
            if not gt_file.exists():
                logger.warning(f"Ground truth not found for {transcript_file.name}")
                continue
            
            print(f"  [{idx}/{len(transcript_files)}] Evaluating {transcript_file.name}...")
            
            result = self.evaluate_single_meeting(transcript_file, gt_file, use_llm)
            results.append(result)
            
            # Show quick summary
            if result["status"] == "success":
                f1 = result["metrics"]["f1_score"]
                quality = result["quality_assessment"]["overall_quality"]
                print(f"      ✓ F1: {f1:.2%} | Quality: {quality}")
        
        # Aggregate metrics
        aggregate = self._aggregate_results(results)
        
        return {
            "summary": aggregate,
            "individual_results": results,
            "evaluation_date": datetime.now().isoformat(),
            "llm_enabled": use_llm,
            "total_meetings": len(results)
        }
    
    def _aggregate_results(self, results: List[Dict]) -> Dict[str, Any]:
        """Aggregate metrics across all meetings."""
        successful_results = [r for r in results if r["status"] == "success"]
        
        if not successful_results:
            return {"status": "no_successful_evaluations"}
        
        # Average metrics
        avg_precision = sum(r["metrics"]["precision"] for r in successful_results) / len(successful_results)
        avg_recall = sum(r["metrics"]["recall"] for r in successful_results) / len(successful_results)
        avg_f1 = sum(r["metrics"]["f1_score"] for r in successful_results) / len(successful_results)
        avg_match_score = sum(r["metrics"]["average_match_score"] for r in successful_results) / len(successful_results)
        
        # Assignee accuracy
        avg_assignee_exact = sum(
            r["assignee_accuracy"]["exact_match_accuracy"] for r in successful_results
        ) / len(successful_results)
        
        avg_assignee_partial = sum(
            r["assignee_accuracy"]["partial_match_accuracy"] for r in successful_results
        ) / len(successful_results)
        
        # Deadline accuracy
        avg_deadline_extraction = sum(
            r["deadline_accuracy"]["deadline_extraction_rate"] for r in successful_results
        ) / len(successful_results)
        
        # Total counts
        total_gt = sum(r["ground_truth_count"] for r in successful_results)
        total_extracted = sum(r["extracted_count"] for r in successful_results)
        total_matched = sum(r["matched_count"] for r in successful_results)
        
        # Quality distribution
        quality_dist = {}
        for result in successful_results:
            quality = result["quality_assessment"]["overall_quality"]
            quality_dist[quality] = quality_dist.get(quality, 0) + 1
        
        return {
            "average_metrics": {
                "precision": avg_precision,
                "recall": avg_recall,
                "f1_score": avg_f1,
                "match_score": avg_match_score
            },
            "assignee_accuracy": {
                "exact_match": avg_assignee_exact,
                "partial_match": avg_assignee_partial
            },
            "deadline_accuracy": {
                "extraction_rate": avg_deadline_extraction
            },
            "totals": {
                "ground_truth_tasks": total_gt,
                "extracted_tasks": total_extracted,
                "matched_tasks": total_matched,
                "meetings_evaluated": len(successful_results)
            },
            "quality_distribution": quality_dist
        }
    
    def generate_report(self, evaluation_results: Dict, output_file: Path):
        """Generate a detailed evaluation report with academic metrics."""
        summary = evaluation_results['summary']
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("# Action Item Extraction - Evaluation Report\n\n")
            f.write(f"**Evaluation Date:** {evaluation_results['evaluation_date']}\n")
            f.write(f"**LLM Enabled:** {evaluation_results['llm_enabled']}\n")
            f.write(f"**Total Meetings:** {evaluation_results['total_meetings']}\n\n")
            
            f.write("## Overall Performance\n\n")
            f.write("### Key Metrics (Academic Standard)\n\n")
            metrics = summary['average_metrics']
            
            # Academic metrics table
            f.write("| Metric | Value | Description |\n")
            f.write("|--------|-------|-------------|\n")
            f.write(f"| **Precision** | {metrics['precision']:.2%} | Proportion of extracted tasks that are correct (TP / (TP + FP)) |\n")
            f.write(f"| **Recall** | {metrics['recall']:.2%} | Proportion of ground truth tasks found (TP / (TP + FN)) |\n")
            f.write(f"| **F1 Score** | {metrics['f1_score']:.2%} | Harmonic mean of precision and recall |\n")
            f.write(f"| **Match Quality** | {metrics['match_score']:.2%} | Average semantic similarity of matched tasks |\n\n")
            
            # Calculate additional academic metrics
            totals = summary['totals']
            tp = totals['matched_tasks']
            fp = totals['extracted_tasks'] - totals['matched_tasks']
            fn = totals['ground_truth_tasks'] - totals['matched_tasks']
            
            f.write("### Confusion Matrix\n\n")
            f.write("| | Predicted Positive | Predicted Negative |\n")
            f.write("|---|---|---|\n")
            f.write(f"| **Actual Positive** | TP = {tp} | FN = {fn} |\n")
            f.write(f"| **Actual Negative** | FP = {fp} | TN = N/A |\n\n")
            
            f.write("### Entity-Level Accuracy\n\n")
            assignee = summary['assignee_accuracy']
            deadline = summary['deadline_accuracy']
            
            f.write("| Entity Type | Exact Match | Partial Match | Notes |\n")
            f.write("|-------------|-------------|---------------|-------|\n")
            f.write(f"| **Assignee** | {assignee['exact_match']:.2%} | {assignee['partial_match']:.2%} | Person extraction accuracy |\n")
            f.write(f"| **Deadline** | {deadline['extraction_rate']:.2%} | N/A | Date extraction rate |\n\n")
            
            f.write("### Task Counts\n\n")
            f.write(f"- **Ground Truth Tasks:** {totals['ground_truth_tasks']}\n")
            f.write(f"- **Extracted Tasks:** {totals['extracted_tasks']}\n")
            f.write(f"- **Successfully Matched:** {totals['matched_tasks']}\n")
            f.write(f"- **False Positives:** {fp}\n")
            f.write(f"- **False Negatives:** {fn}\n\n")
            
            f.write("### Quality Distribution\n\n")
            for quality, count in sorted(summary['quality_distribution'].items()):
                percentage = (count / totals['meetings_evaluated']) * 100
                f.write(f"- **{quality}:** {count} meetings ({percentage:.1f}%)\n")
            
            # Performance analysis
            f.write("\n## Performance Analysis\n\n")
            
            if metrics['precision'] < 0.5:
                f.write("⚠️ **Low Precision Alert**: The system is extracting too many false positives. ")
                f.write("Consider increasing confidence thresholds or improving task pattern matching.\n\n")
            elif metrics['precision'] >= 0.8:
                f.write("✅ **High Precision**: The system has few false positives. ")
                f.write("Extracted tasks are highly reliable.\n\n")
            
            if metrics['recall'] < 0.5:
                f.write("⚠️ **Low Recall Alert**: The system is missing many ground truth tasks. ")
                f.write("Consider expanding pattern coverage or reducing confidence thresholds.\n\n")
            elif metrics['recall'] >= 0.8:
                f.write("✅ **High Recall**: The system finds most ground truth tasks effectively.\n\n")
            
            if assignee['exact_match'] < 0.4:
                f.write("⚠️ **Assignee Extraction Issue**: Low accuracy in extracting correct assignees. ")
                f.write("Review person name extraction logic and speaker diarization.\n\n")
            
            if deadline['extraction_rate'] < 0.5:
                f.write("⚠️ **Deadline Extraction Issue**: Low rate of deadline extraction. ")
                f.write("Review date parsing and temporal expression recognition.\n\n")
            
            f.write("\n## Detailed Results by Meeting\n\n")
            f.write("| Meeting | Type | F1 | Precision | Recall | Quality | GT/Ext/Match |\n")
            f.write("|---------|------|----|-----------| -------|---------|-------------|\n")
            
            for result in evaluation_results['individual_results']:
                if result['status'] != 'success':
                    continue
                
                name = result['transcript_file']
                mtype = result['meeting_type'][:15]  # Truncate for table
                f1 = result['metrics']['f1_score']
                prec = result['metrics']['precision']
                rec = result['metrics']['recall']
                qual = result['quality_assessment']['overall_quality']
                gt = result['ground_truth_count']
                ext = result['extracted_count']
                match = result['matched_count']
                
                f.write(f"| {name} | {mtype} | {f1:.2f} | {prec:.2f} | {rec:.2f} | {qual} | {gt}/{ext}/{match} |\n")
            
            f.write("\n---\n\n")
            f.write("*This report uses standard academic metrics for information extraction evaluation.*\n")
        
        print(f"\n📄 Report saved to: {output_file}")


if __name__ == "__main__":
    import sys
    
    # Usage: python action_item_evaluator.py [test_data_dir] [--llm | --pure-llm]
    test_data_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("evaluation/test_data_50")
    
    # Check extraction method
    if "--pure-llm" in sys.argv:
        use_llm = True  # Pure LLM extraction
        use_llm_fallback = False
        method_name = "pure_llm"
    elif "--llm" in sys.argv:
        use_llm = False  # Rule-based with LLM fallback
        use_llm_fallback = True
        method_name = "with_llm"
    else:
        use_llm = False  # Pure rule-based
        use_llm_fallback = False
        method_name = "no_llm"
    
    evaluator = ActionItemEvaluator()
    evaluator.use_pure_llm = use_llm  # Add attribute to pass to extraction
    evaluator.use_llm_fallback = use_llm_fallback
    
    results = evaluator.evaluate_batch(test_data_dir, use_llm=use_llm_fallback)
    
    # Generate report
    report_file = test_data_dir / f"evaluation_report_{method_name}.md"
    evaluator.generate_report(results, report_file)
    
    print(f"\n✅ Evaluation complete!")
    print(f"\n📊 Summary:")
    summary = results['summary']
    print(f"   F1 Score: {summary['average_metrics']['f1_score']:.2%}")
    print(f"   Precision: {summary['average_metrics']['precision']:.2%}")
    print(f"   Recall: {summary['average_metrics']['recall']:.2%}")
    print(f"   Assignee Accuracy: {summary['assignee_accuracy']['exact_match']:.2%}")
    print(f"   Deadline Extraction: {summary['deadline_accuracy']['extraction_rate']:.2%}")
    print(f"\n📈 Quality Distribution:")
    for quality, count in sorted(summary['quality_distribution'].items(), key=lambda x: x[1], reverse=True):
        print(f"   {quality}: {count} meetings")
    print(f"\n📁 Detailed report: {report_file}")
