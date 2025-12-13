from summarization.core.meeting_summarizer import MeetingSummarizer
from typing import Dict, Optional, Any


def summarize_meeting(
        transcript_file_path: str,
        model_name: str = "facebook/bart-large-cnn",
        output_format: str = "json",
        output_file: Optional[str] = None,
        extract_action_items: bool = True,
        summary_length: Dict[str, int] = {"max": 150, "min": 30}
) -> Dict[str, Any]:
    summarizer = MeetingSummarizer(
        model_path=model_name
    )

    # Load transcript data
    import json
    with open(transcript_file_path, 'r', encoding='utf-8') as f:
        transcript_data = json.load(f)

    # Generate summary
    summary_results = summarizer.summarize(
        transcript_data,
        include_action_items=extract_action_items,
        max_summary_length=summary_length["max"],
        min_summary_length=summary_length["min"]
    )

    # Save summary if output file specified
    if output_file:
        if output_format == "json":
            summarizer.save_summary(summary_results, output_file)
        elif output_format == "txt":
            summarizer.save_text_summary(summary_results, output_file)
        elif output_format == "md":
            summarizer.save_markdown_summary(summary_results, output_file)

    return summary_results