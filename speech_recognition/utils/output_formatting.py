"""
Output formatting utilities for the speech recognition package.
"""

import os
import json
from typing import Dict, List, Any

from speech_recognition.utils.logging_setup import setup_logger

logger = setup_logger("OutputFormatting")


def save_output(result: Dict[str, Any], output_format: str, output_file: str) -> None:
    """
    Save the transcription result to a file.

    Args:
        result: Transcription result
        output_format: Format for the output file
        output_file: Path to save the output file
    """
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
                    # Speaker-separated transcript
                    for segment in result["transcript"]:
                        speaker = f"[{segment['speaker']}]: " if "speaker" in segment else ""
                        f.write(f"{speaker}{segment['text']}\n")
                else:
                    # Plain transcript
                    f.write(result["full_text"])

        elif output_format.lower() == "srt":
            write_srt(result["transcript"], output_file)

        elif output_format.lower() == "vtt":
            write_vtt(result["transcript"], output_file)

        else:
            logger.warning(f"Unsupported output format: {output_format}")

        logger.info(f"Output saved to {output_file}")

    except Exception as e:
        logger.error(f"Failed to save output: {str(e)}", exc_info=True)


def write_srt(transcript: List[Dict[str, Any]], output_file: str) -> None:
    """
    Write transcript in SRT subtitle format (without timestamps since they're removed).

    Args:
        transcript: Formatted transcript
        output_file: Path to save the SRT file
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        for i, segment in enumerate(transcript, 1):
            # Add speaker label if available
            text = segment["text"]
            if "speaker" in segment:
                text = f"[{segment['speaker']}] {text}"

            f.write(f"{i}\n")
            # Use dummy timestamps for SRT format requirement
            f.write(f"00:00:00,000 --> 00:00:00,000\n")
            f.write(f"{text}\n\n")


def write_vtt(transcript: List[Dict[str, Any]], output_file: str) -> None:
    """
    Write transcript in WebVTT subtitle format (without timestamps since they're removed).

    Args:
        transcript: Formatted transcript
        output_file: Path to save the VTT file
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("WEBVTT\n\n")

        for i, segment in enumerate(transcript, 1):
            # Add speaker label if available
            text = segment["text"]
            if "speaker" in segment:
                text = f"[{segment['speaker']}] {text}"

            f.write(f"{i}\n")
            # Use dummy timestamps for VTT format requirement
            f.write(f"00:00:00.000 --> 00:00:00.000\n")
            f.write(f"{text}\n\n")


def format_transcript(
        result: Dict[str, Any],
        speaker_segments: List[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Format transcript with speaker labels, removing timestamps.

    Args:
        result: Whisper transcription result
        speaker_segments: Speaker diarization segments (optional)

    Returns:
        Formatted transcript with speaker information
    """
    formatted_transcript = []

    # Process based on whether speaker segments are available
    if speaker_segments:
        # When speaker diarization is available, use speaker segments
        for segment in speaker_segments:
            formatted_transcript.append({
                "text": segment["text"],
                "speaker": segment["speaker"]
            })
    else:
        # Without speaker diarization, use Whisper segments
        if "segments" in result:
            for segment in result["segments"]:
                formatted_transcript.append({
                    "text": segment["text"]
                })
        else:
            # If no segments, use full text
            formatted_transcript.append({
                "text": result["text"]
            })

    return formatted_transcript


def create_error_response(error_message: str) -> Dict[str, Any]:
    """Create an error response dictionary."""
    return {
        "status": "error",
        "message": error_message
    }