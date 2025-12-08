"""
Meeting Assistant AI - Full Pipeline
=====================================
This script runs the complete meeting processing pipeline:
1. Transcription (Whisper API)
2. Summarization (LLM)
3. Action Item Extraction (LLM)

Usage:
    python pipeline.py <audio_file>
    python pipeline.py speech_recognition/samples/marketing_meeting.mp3
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def print_header(title: str):
    """Print a formatted header"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_step(step_num: int, title: str):
    """Print a step indicator"""
    print(f"\n{'─' * 60}")
    print(f"  Step {step_num}: {title}")
    print(f"{'─' * 60}")


def run_pipeline(
    audio_file: str,
    output_dir: str = "outputs/pipeline",
    language: str = None,
    skip_transcription: bool = False,
    transcript_file: str = None
):
    """
    Run the full meeting processing pipeline.
    
    Args:
        audio_file: Path to the audio/video file
        output_dir: Directory for output files
        language: Language code (auto-detect if None)
        skip_transcription: Skip transcription step (use existing transcript)
        transcript_file: Path to existing transcript file (if skipping transcription)
    """
    start_time = datetime.now()
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Get base name for output files
    audio_path = Path(audio_file)
    base_name = audio_path.stem
    
    print_header("Meeting Assistant AI - Full Pipeline")
    print(f"\n📁 Input: {audio_file}")
    print(f"📂 Output: {output_dir}")
    print(f"🕐 Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # =========================================================================
    # Step 1: Transcription
    # =========================================================================
    print_step(1, "Transcription (Groq Whisper API)")
    
    if skip_transcription and transcript_file:
        print(f"⏭️  Skipping transcription, using: {transcript_file}")
        transcript_path = transcript_file
        with open(transcript_path, 'r', encoding='utf-8') as f:
            transcript_data = json.load(f)
    else:
        from speech_recognition import Transcriber
        
        print("🎤 Initializing transcriber...")
        transcriber = Transcriber()
        
        print(f"🔊 Transcribing audio file...")
        result = transcriber.transcribe(
            input_path=audio_file,
            language=language,
            detect_speakers=True
        )
        
        # Save transcript
        transcript_path = output_path / f"{base_name}_transcript.json"
        transcriber.save(result, str(transcript_path), "json")
        
        # Also save SRT for reference
        srt_path = output_path / f"{base_name}_transcript.srt"
        transcriber.save(result, str(srt_path), "srt")
        
        print(f"\n✅ Transcription completed!")
        print(f"   Duration: {result.duration:.1f} seconds")
        print(f"   Language: {result.language}")
        print(f"   Segments: {len(result.segments)}")
        print(f"   Processing time: {result.processing_time:.1f}s")
        print(f"   Saved: {transcript_path}")
        
        # Load transcript data for next steps
        with open(transcript_path, 'r', encoding='utf-8') as f:
            transcript_data = json.load(f)
    
    # =========================================================================
    # Step 2: Summarization
    # =========================================================================
    print_step(2, "Summarization (LLM)")
    
    from summarization.llm_summarizer import LLMSummarizer
    
    print("📝 Generating meeting summary with LLM...")
    
    summary_path = output_path / f"{base_name}_summary.json"
    summary_md_path = output_path / f"{base_name}_summary.md"
    
    llm_summarizer = LLMSummarizer()
    summary_result_obj = llm_summarizer.summarize(transcript_data)
    
    # Save both JSON and Markdown
    llm_summarizer.save_json(summary_result_obj, str(summary_path))
    llm_summarizer.save_markdown(summary_result_obj, str(summary_md_path))
    
    summary_result = llm_summarizer.to_dict(summary_result_obj)
    
    print(f"\n✅ Summarization completed!")
    print(f"   Processing time: {summary_result_obj.processing_time:.1f}s")
    print(f"   Saved: {summary_path}")
    print(f"   Saved: {summary_md_path}")
    
    # Print summary preview
    print(f"\n📋 Title: {summary_result_obj.title}")
    print(f"\n📋 Overview:\n   {summary_result_obj.overview}")
    
    if summary_result_obj.key_points:
        print(f"\n🔑 Key Points:")
        for point in summary_result_obj.key_points[:5]:
            print(f"   • {point}")
        if len(summary_result_obj.key_points) > 5:
            print(f"   ... and {len(summary_result_obj.key_points) - 5} more")
    
    # =========================================================================
    # Step 3: Action Item Extraction
    # =========================================================================
    print_step(3, "Action Item Extraction (LLM)")
    
    from action_item_extraction.extractor import extract_action_items
    
    print("🎯 Extracting action items with LLM...")
    
    action_items_path = output_path / f"{base_name}_action_items.json"
    
    action_result = extract_action_items(
        transcript_data=transcript_data,
        output_file=str(action_items_path),
        use_llm=True  # Use LLM-based extraction
    )
    
    tasks = action_result.get('action_items', [])
    
    print(f"\n✅ Action item extraction completed!")
    print(f"   Total items: {len(tasks)}")
    print(f"   Method: {action_result.get('extraction_method', 'llm')}")
    print(f"   Saved: {action_items_path}")
    
    # Print action items
    if tasks:
        print(f"\n🎯 Action Items Found:")
        for i, task in enumerate(tasks, 1):
            assignee = task.get('assignee', 'Unassigned')
            description = task.get('description', '')
            due_date = task.get('due_date', '')
            
            due_str = f" (Due: {due_date})" if due_date else ""
            print(f"   {i}. [{assignee}] {description}{due_str}")
    
    # =========================================================================
    # Generate Final Report
    # =========================================================================
    print_step(4, "Generating Final Report")
    
    report_path = output_path / f"{base_name}_report.md"
    
    # Get summary data from Groq summarizer format
    executive_summary = summary_result.get('executive_summary', '')
    key_points = summary_result.get('key_points', [])
    topics = summary_result.get('topics', [])
    decisions = summary_result.get('decisions', [])
    participants = summary_result.get('participants', [])
    next_steps = summary_result.get('next_steps', [])
    
    # Generate comprehensive markdown report
    report_content = f"""# 📊 Meeting Report: {base_name}

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Audio File:** {audio_file}  
**Duration:** {transcript_data.get('metadata', {}).get('duration', 'N/A')} seconds  
**Segments:** {len(transcript_data.get('segments', []))}

---

## 📋 Executive Summary

{executive_summary}

"""
    
    if participants:
        report_content += "## 👥 Participants\n\n"
        for p in participants:
            report_content += f"- {p}\n"
        report_content += "\n"
    
    if key_points:
        report_content += "## 🔑 Key Points\n\n"
        for point in key_points:
            report_content += f"- {point}\n"
        report_content += "\n"
    
    if topics:
        report_content += "## 📌 Topics Discussed\n\n"
        for topic in topics:
            report_content += f"- {topic}\n"
        report_content += "\n"
    
    if decisions:
        report_content += "## ✅ Decisions Made\n\n"
        for decision in decisions:
            report_content += f"- {decision}\n"
        report_content += "\n"
    
    if next_steps:
        report_content += "## ➡️ Next Steps\n\n"
        for step in next_steps:
            report_content += f"- {step}\n"
        report_content += "\n"
    
    report_content += "## 🎯 Action Items\n\n"
    
    if tasks:
        report_content += "| # | Assignee | Task | Due Date | Speaker |\n"
        report_content += "|---|----------|------|----------|----------|\n"
        for i, task in enumerate(tasks, 1):
            assignee = task.get('assignee', 'Unassigned')
            description = task.get('description', '')
            due_date = task.get('due_date', '-')
            speaker = task.get('speaker', '-')
            report_content += f"| {i} | {assignee} | {description} | {due_date} | {speaker} |\n"
    else:
        report_content += "*No action items identified.*\n"
    
    report_content += f"""
---

## 📁 Output Files

- Transcript (JSON): `{base_name}_transcript.json`
- Transcript (SRT): `{base_name}_transcript.srt`
- Summary (JSON): `{base_name}_summary.json`
- Summary (Markdown): `{base_name}_summary.md`
- Action Items: `{base_name}_action_items.json`
- This Report: `{base_name}_report.md`
"""
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    print(f"✅ Report generated: {report_path}")
    
    # =========================================================================
    # Pipeline Complete
    # =========================================================================
    end_time = datetime.now()
    total_time = (end_time - start_time).total_seconds()
    
    print_header("Pipeline Complete!")
    print(f"\n⏱️  Total processing time: {total_time:.1f} seconds")
    print(f"\n📂 Output files saved to: {output_dir}")
    print(f"   • {base_name}_transcript.json")
    print(f"   • {base_name}_transcript.srt")
    print(f"   • {base_name}_summary.json")
    print(f"   • {base_name}_action_items.json")
    print(f"   • {base_name}_report.md")
    
    return {
        'transcript': str(transcript_path) if not skip_transcription else transcript_file,
        'summary': str(summary_path),
        'action_items': str(action_items_path),
        'report': str(report_path),
        'processing_time': total_time
    }


def main():
    parser = argparse.ArgumentParser(
        description="Meeting Assistant AI - Full Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python pipeline.py speech_recognition/samples/marketing_meeting.mp3
  python pipeline.py meeting.wav -o outputs/my_meeting
  python pipeline.py meeting.mp4 -l en --skip-transcription -t existing_transcript.json
        """
    )
    
    parser.add_argument(
        "audio_file",
        help="Path to audio or video file"
    )
    
    parser.add_argument(
        "-o", "--output",
        default="outputs/pipeline",
        help="Output directory (default: outputs/pipeline)"
    )
    
    parser.add_argument(
        "-l", "--language",
        default=None,
        help="Language code (e.g., en, tr). Auto-detected if not specified"
    )
    
    parser.add_argument(
        "--skip-transcription",
        action="store_true",
        help="Skip transcription step"
    )
    
    parser.add_argument(
        "-t", "--transcript",
        default=None,
        help="Path to existing transcript file (use with --skip-transcription)"
    )
    
    args = parser.parse_args()
    
    # Validate input file
    if not Path(args.audio_file).exists():
        print(f"Error: Input file not found: {args.audio_file}", file=sys.stderr)
        sys.exit(1)
    
    # Run pipeline
    try:
        run_pipeline(
            audio_file=args.audio_file,
            output_dir=args.output,
            language=args.language,
            skip_transcription=args.skip_transcription,
            transcript_file=args.transcript
        )
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
