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