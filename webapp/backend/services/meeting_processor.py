import sys
import asyncio
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from speech_recognition import MeetingTranscriber
from summarization.llm_summarizer import LLMSummarizer
from action_item_extraction.ml_extractor import LLMActionItemExtractor
from llm_diarization import LLMDiarizer

from config import WHISPER_MODEL
from database import async_session
from db_models import Meeting, Task
from sqlalchemy import select

# Import processing_jobs from meetings route
from routes.meetings import processing_jobs


async def update_job_status(job_id: str, **kwargs):
    # Update in-memory status
    if job_id in processing_jobs:
        processing_jobs[job_id].update(kwargs)
    
    # Update in database
    async with async_session() as session:
        result = await session.execute(
            select(Meeting).where(Meeting.job_id == job_id)
        )
        meeting = result.scalar_one_or_none()
        if meeting:
            for key, value in kwargs.items():
                if hasattr(meeting, key):
                    setattr(meeting, key, value)
            await session.commit()


async def process_meeting_db(job_id: str, file_path: Path, filename: str, user_id: str):
    start_time = datetime.now()
    
    try:
        # Step 1: Transcription with local Whisper
        await update_job_status(
            job_id, 
            step="transcription", 
            progress=10, 
            message="Transcribing audio with Whisper..."
        )
        
        transcriber = MeetingTranscriber(
            model_name=WHISPER_MODEL,
            language=None,
            enable_speaker_diarization=False
        )
        
        transcript_result = transcriber.transcribe_audio(
            str(file_path),
            segment_by_speaker=False
        )
        
        if transcript_result.get("status") == "error":
            raise Exception(transcript_result.get("message", "Transcription failed"))
        
        await update_job_status(
            job_id, 
            progress=35, 
            message="Transcription complete. Generating summary..."
        )
        
        # Convert to standard format
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
        await update_job_status(
            job_id, 
            step="summarization", 
            progress=40, 
            message="Generating summary..."
        )
        
        summarizer = LLMSummarizer()
        summary_result = summarizer.summarize(transcript_data)
        summary_dict = summarizer.to_dict(summary_result)
        
        await update_job_status(
            job_id, 
            progress=55, 
            message="Summary generated. Extracting tasks..."
        )
        
        # Step 3: Task Extraction
        await update_job_status(
            job_id, 
            step="extraction", 
            progress=60
        )
        
        extractor = LLMActionItemExtractor()
        tasks_result = extractor.extract_action_items(transcript_data)
        
        await update_job_status(
            job_id, 
            progress=80, 
            message="Tasks extracted. Identifying speakers..."
        )
        
        # Step 4: LLM-based Speaker Diarization
        await update_job_status(
            job_id, 
            step="diarization", 
            progress=90, 
            message="Analyzing speakers with AI..."
        )
        
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
        
        # Step 5: Save to database
        processing_time = (datetime.now() - start_time).total_seconds()
        
        async with async_session() as session:
            # Get meeting
            result = await session.execute(
                select(Meeting).where(Meeting.job_id == job_id)
            )
            meeting = result.scalar_one_or_none()
            
            if meeting:
                # Update meeting with results
                meeting.status = "completed"
                meeting.step = "done"
                meeting.progress = 100
                meeting.message = "Processing complete!"
                meeting.completed_at = datetime.utcnow()
                meeting.duration = transcript_data["metadata"]["duration"]
                meeting.language = transcript_data["metadata"]["language"]
                meeting.processing_time = processing_time
                meeting.transcript = diarized_transcript
                meeting.summary = summary_dict
                
                # Create tasks
                for i, task_data in enumerate(tasks_result.get('action_items', [])):
                    task = Task(
                        task_id=f"{job_id}-task-{i}",
                        meeting_id=meeting.id,
                        description=task_data.get('description', ''),
                        assignee=task_data.get('assignee'),
                        due_date=task_data.get('due_date'),
                        priority=task_data.get('priority', 'Medium'),
                        speaker=task_data.get('speaker'),
                        confidence=task_data.get('confidence'),
                    )
                    session.add(task)
                
                await session.commit()
        
        # Update in-memory status
        if job_id in processing_jobs:
            processing_jobs[job_id].update({
                "status": "completed",
                "step": "done",
                "progress": 100,
                "message": "Processing complete!",
                "completed_at": datetime.now().isoformat()
            })
        
    except Exception as e:
        # Update error status
        await update_job_status(
            job_id,
            status="failed",
            error=str(e),
            message=f"Error: {str(e)}"
        )
        if job_id in processing_jobs:
            processing_jobs[job_id].update({
                "status": "failed",
                "error": str(e),
                "message": f"Error: {str(e)}"
            })
        raise
    
    finally:
        # Cleanup uploaded file
        if file_path.exists():
            file_path.unlink()
