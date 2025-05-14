"""
Example usage for the Meeting Assistant AI summarization module.
"""

from summarization.summarizer import summarize_meeting
from summarization.core.meeting_summarizer import MeetingSummarizer

# Method 1: Using the utility function (simplest approach)
result = summarize_meeting(
    "../outputs/transcript.json",
    model_name="facebook/bart-large-cnn",  # Or path to your fine-tuned model
    output_format="md",
    output_file="../outputs/meeting_summary.md",
    extract_action_items=True,
    summary_length={"max": 150, "min": 30}
)

print(f"Summary generated with {len(result['summary']['key_topics'])} key topics identified")

# Method 2: Using the MeetingSummarizer class directly (more control)
'''summarizer = MeetingSummarizer(
    model_path="facebook/bart-large-cnn"  # Or path to your fine-tuned model
)

# Load transcript data
import json
with open("../outputs/transcript.json", 'r', encoding='utf-8') as f:
    transcript_data = json.load(f)

# Generate summary with custom parameters
summary_results = summarizer.summarize(
    transcript_data,
    include_action_items=True,
    max_summary_length=200,
    min_summary_length=50,
    num_extractive_sentences=7
)

# Save in different formats
summarizer.save_summary(summary_results, "./outputs/meeting_summary.json")
summarizer.save_text_summary(summary_results, "./outputs/meeting_summary.txt")
summarizer.save_markdown_summary(summary_results, "./outputs/meeting_summary.md")

print("Summary generated and saved in multiple formats")'''