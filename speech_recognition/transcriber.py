"""
Main interface for the Whisper-based meeting transcriber.
This file provides the primary interface for using the transcription functionality.
"""

from speech_recognition.core.meeting_transcriber import MeetingTranscriber
from typing import Dict, Optional, Any


def transcribe_meeting(
        audio_file_path: str,
        model_name: str = "base",
        output_format: str = "json",
        output_file: Optional[str] = None,
        enable_speaker_diarization: bool = False,
        language: str = "en"
) -> Dict[str, Any]:
    """
    Utility function to transcribe a meeting audio file with Whisper.

    Args:
        audio_file_path: Path to the audio file
        model_name: Name of the Whisper model to use ("tiny", "base", "small", "medium", "large")
        output_format: Format for output ("json", "txt", "srt", "vtt")
        output_file: Path to save the output file (optional)
        enable_speaker_diarization: Whether to enable speaker diarization
        language: Language code for transcription

    Returns:
        Transcription result dictionary
    """
    transcriber = MeetingTranscriber(
        model_name=model_name,
        language=language,
        enable_speaker_diarization=enable_speaker_diarization
    )

    return transcriber.transcribe_audio(
        audio_file_path,
        output_format=output_format,
        output_file=output_file,
        segment_by_speaker=enable_speaker_diarization
    )