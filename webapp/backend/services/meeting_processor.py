"""
Meeting Processing Service
==========================
Background processing for meeting transcription, summarization, and task extraction.
"""

import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from speech_recognition import MeetingTranscriber
from summarization.llm_summarizer import LLMSummarizer
from action_item_extraction.ml_extractor import LLMActionItemExtractor
from llm_diarization import LLMDiarizer

from config import WHISPER_MODEL
from storage import jobs, results, user_mappings, assignee_mappings
from models import MeetingResult, TranscriptSegment, TaskItem


def process_meeting(job_id: str, file_path: Path, filename: str):
    """Background task to process meeting file"""
    start_time = datetime.now()
    
    try:
        # Step 1: Transcription with local Whisper (no diarization)
        jobs[job_id]["step"] = "transcription"
        jobs[job_id]["progress"] = 10
        jobs[job_id]["message"] = "Transcribing audio with Whisper..."
        
        transcriber = MeetingTranscriber(
            model_name=WHISPER_MODEL,
            language=None,  # Auto-detect language
            enable_speaker_diarization=False  # Diarization disabled
        )
        
        transcript_result = transcriber.transcribe_audio(
            str(file_path),
            segment_by_speaker=False
        )
        
        if transcript_result.get("status") == "error":
            raise Exception(transcript_result.get("message", "Transcription failed"))
        
        jobs[job_id]["progress"] = 35
        jobs[job_id]["message"] = "Transcription complete. Generating summary..."
        
        # Convert to standard format (without speaker for task extraction)
        raw_transcript = [
            {
                "text": seg.get("text", ""),
                "start": seg.get("start", 0),
                "end": seg.get("end", 0)
            }
            for seg in transcript_result["transcript"]
        ]
        
        transcript_data = {
            "metadata": {
                "file": filename,
                "duration": transcript_result["metadata"]["duration"],
                "language": transcript_result["metadata"].get("language") or "unknown"
            },
            "transcript": raw_transcript
        }
        
        # Step 2: Summarization
        jobs[job_id]["step"] = "summarization"
        jobs[job_id]["progress"] = 40
        jobs[job_id]["message"] = "Generating summary..."
        
        summarizer = LLMSummarizer()
        summary_result = summarizer.summarize(transcript_data)
        summary_dict = summarizer.to_dict(summary_result)
        
        jobs[job_id]["progress"] = 55
        jobs[job_id]["message"] = "Summary generated. Extracting tasks..."
        
        # Step 3: Task Extraction (without speaker field - LLM extracts names from text)
        jobs[job_id]["step"] = "extraction"
        jobs[job_id]["progress"] = 60
        
        extractor = LLMActionItemExtractor()
        tasks_result = extractor.extract_action_items(transcript_data)
        
        # Convert tasks to our format with IDs
        tasks = []
        unique_assignees = set()
        for i, task in enumerate(tasks_result.get('action_items', [])):
            task_item = TaskItem(
                id=f"{job_id}-task-{i}",
                description=task.get('description', ''),
                assignee=task.get('assignee'),
                due_date=task.get('due_date'),
                priority=task.get('priority', 'Medium'),
                speaker=task.get('speaker'),
                confidence=task.get('confidence')
            )
            # Track unique assignees for mapping
            if task_item.assignee and task_item.assignee.lower() != 'unassigned':
                unique_assignees.add(task_item.assignee)
            # Try to auto-map assignee
            if task_item.assignee and task_item.assignee in user_mappings:
                task_item.jira_assignee_id = user_mappings[task_item.assignee]
            tasks.append(task_item)
        
        # Initialize assignee mappings for this job
        assignee_mappings[job_id] = {name: None for name in unique_assignees}
        
        jobs[job_id]["progress"] = 80
        jobs[job_id]["message"] = "Tasks extracted. Identifying speakers..."
        
        # Step 4: LLM-based Speaker Diarization (for transcript display only)
        jobs[job_id]["step"] = "diarization"
        jobs[job_id]["progress"] = 90
        jobs[job_id]["message"] = "Analyzing speakers with AI..."
        
        # Add speaker field for diarization
        transcript_for_diarization = [
            {
                "speaker": "Unknown",
                "text": seg.get("text", ""),
                "start": seg.get("start", 0),
                "end": seg.get("end", 0)
            }
            for seg in raw_transcript
        ]
        
        diarizer = LLMDiarizer()
        diarized_transcript = diarizer.diarize_transcript(transcript_for_diarization)
        
        # Update transcript_data with diarized version
        transcript_data["transcript"] = diarized_transcript
        
        # Step 5: Complete
        jobs[job_id]["step"] = "done"
        jobs[job_id]["progress"] = 100
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["message"] = "Processing complete!"
        jobs[job_id]["completed_at"] = datetime.now().isoformat()
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # Store result
        results[job_id] = MeetingResult(
            job_id=job_id,
            filename=filename,
            duration=transcript_data["metadata"]["duration"],
            language=transcript_data["metadata"]["language"],
            transcript=[TranscriptSegment(**seg) for seg in transcript_data["transcript"]],
            summary=summary_dict,
            tasks=tasks,
            created_at=jobs[job_id]["created_at"],
            processing_time=processing_time
        ).model_dump()
        
    except Exception as e:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)
        jobs[job_id]["message"] = f"Error: {str(e)}"
        raise
    
    finally:
        # Cleanup uploaded file
        if file_path.exists():
            file_path.unlink()
