import os
import json
from typing import Dict, List, Any

from speech_recognition.utils.logging_setup import setup_logger

logger = setup_logger("OutputFormatting")


def save_output(result: Dict[str, Any], output_format: str, output_file: str) -> None:
    try:
        # Create directory if it doesn't exist
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Save based on format
        if output_format.lower() == "json":
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)

        elif output_format.lower() == "txt":
            with open(output_file, 'w', encoding='utf-8') as f:
                if any("speaker" in segment for segment in result["transcript"]):
                    # Speaker-separated transcript with timestamps
                    for segment in result["transcript"]:
                        timestamp = format_timestamp(segment.get("start", 0), segment.get("end", 0))
                        speaker = f"[{segment['speaker']}]: " if "speaker" in segment else ""
                        f.write(f"{timestamp} {speaker}{segment['text']}\n")
                else:
                    # Plain transcript with timestamps
                    for segment in result["transcript"]:
                        timestamp = format_timestamp(segment.get("start", 0), segment.get("end", 0))
                        f.write(f"{timestamp} {segment['text']}\n")

        elif output_format.lower() == "srt":
            write_srt(result["transcript"], output_file)

        elif output_format.lower() == "vtt":
            write_vtt(result["transcript"], output_file)

        else:
            logger.warning(f"Unsupported output format: {output_format}")

        logger.info(f"Output saved to {output_file}")

    except Exception as e:
        logger.error(f"Failed to save output: {str(e)}", exc_info=True)


def format_timestamp(start_time: float, end_time: float) -> str:
    return f"[{format_time(start_time)} - {format_time(end_time)}]"


def format_time(seconds: float) -> str:
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds_remainder = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds_remainder:06.3f}"


def format_srt_time(seconds: float) -> str:
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds_int = int(seconds % 60)
    milliseconds = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds_int:02d},{milliseconds:03d}"


def format_vtt_time(seconds: float) -> str:
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds_int = int(seconds % 60)
    milliseconds = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds_int:02d}.{milliseconds:03d}"


def write_srt(transcript: List[Dict[str, Any]], output_file: str) -> None:
    with open(output_file, 'w', encoding='utf-8') as f:
        for i, segment in enumerate(transcript, 1):
            # Add speaker label if available
            text = segment["text"]
            if "speaker" in segment:
                text = f"[{segment['speaker']}] {text}"

            # Get timestamps (default to 0 if not available)
            start_time = segment.get("start", 0)
            end_time = segment.get("end", 0)

            f.write(f"{i}\n")
            f.write(f"{format_srt_time(start_time)} --> {format_srt_time(end_time)}\n")
            f.write(f"{text}\n\n")


def write_vtt(transcript: List[Dict[str, Any]], output_file: str) -> None:
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("WEBVTT\n\n")

        for i, segment in enumerate(transcript, 1):
            # Add speaker label if available
            text = segment["text"]
            if "speaker" in segment:
                text = f"[{segment['speaker']}] {text}"

            # Get timestamps (default to 0 if not available)
            start_time = segment.get("start", 0)
            end_time = segment.get("end", 0)

            f.write(f"{i}\n")
            f.write(f"{format_vtt_time(start_time)} --> {format_vtt_time(end_time)}\n")
            f.write(f"{text}\n\n")


def format_transcript(
        result: Dict[str, Any],
        speaker_segments: List[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    formatted_transcript = []

    # Process based on whether speaker segments are available
    if speaker_segments:
        # When speaker diarization is available, use speaker segments (which have timestamps)
        for segment in speaker_segments:
            formatted_transcript.append({
                "text": segment["text"],
                "speaker": segment["speaker"],
                "start": segment["start"],
                "end": segment["end"]
            })
    else:
        # Without speaker diarization, use Whisper segments
        if "segments" in result:
            for segment in result["segments"]:
                formatted_transcript.append({
                    "text": segment["text"],
                    "start": segment["start"],
                    "end": segment["end"]
                })
        else:
            # If no segments, use full text (no timestamps available)
            formatted_transcript.append({
                "text": result["text"],
                "start": 0,
                "end": 0
            })

    return formatted_transcript


def create_error_response(error_message: str) -> Dict[str, Any]:
    return {
        "status": "error",
        "message": error_message
    }