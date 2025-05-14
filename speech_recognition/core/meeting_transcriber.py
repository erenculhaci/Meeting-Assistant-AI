"""
Core implementation of the meeting transcriber with timestamp support.
"""

import os
from datetime import datetime
from typing import Dict, List, Union, Optional, Any

from speech_recognition.core.config import SUPPORTED_FORMATS, WHISPER_MODELS, DEFAULT_DIARIZATION_MODEL
from speech_recognition.models.whisper_model import WhisperTranscriber
from speech_recognition.models.diarization_model import SpeakerDiarizer
from speech_recognition.utils.audio_processing import process_audio_file, detect_audio_issues
from speech_recognition.utils.output_formatting import save_output, format_transcript, create_error_response
from speech_recognition.utils.logging_setup import setup_logger

logger = setup_logger()


class MeetingTranscriber:
    """
    A comprehensive tool for transcribing audio recordings of meetings with
    support for multiple formats, speaker diarization using Whisper AI,
    and timestamp inclusion.
    """

    def __init__(
            self,
            model_name: str = "base",
            device: Optional[str] = None,
            language: str = "en",
            enable_speaker_diarization: bool = False,
            diarization_model: str = DEFAULT_DIARIZATION_MODEL,
            custom_vocabulary: List[str] = None,
            include_timestamps: bool = True
    ):
        """
        Initialize the MeetingTranscriber with Whisper and PyAnnote.

        Args:
            model_name: Whisper model size ("tiny", "base", "small", "medium", "large", "large-v2", "large-v3")
            device: Device to run inference on ("cpu", "cuda", or None for auto-detection)
            language: Language code for transcription
            enable_speaker_diarization: Whether to enable speaker diarization
            diarization_model: PyAnnote model to use for speaker diarization
            custom_vocabulary: List of domain-specific terms to improve recognition
            include_timestamps: Whether to include timestamps in output (default: True)
        """
        self.language = language
        self.custom_vocabulary = custom_vocabulary
        self.enable_speaker_diarization = enable_speaker_diarization
        self.include_timestamps = include_timestamps

        # Initialize Whisper model
        self.transcriber = WhisperTranscriber(
            model_name=model_name,
            device=device,
            language=language
        )

        # Initialize speaker diarization if requested
        self.diarizer = None
        if enable_speaker_diarization:
            self.diarizer = SpeakerDiarizer(
                model_name=diarization_model,
                device=device
            )
            # Update the diarization flag based on successful initialization
            self.enable_speaker_diarization = self.diarizer.is_available()

    def transcribe_audio(
            self,
            audio_file_path: str,
            output_format: str = "json",
            output_file: Optional[str] = None,
            segment_by_speaker: bool = False,
    ) -> Dict[str, Any]:
        """
        Transcribe an audio file to text using Whisper.

        Args:
            audio_file_path: Path to the audio file
            output_format: Format for the output ("json", "txt", "srt", "vtt")
            output_file: Path to save the output file (optional)
            segment_by_speaker: Whether to segment by speaker (requires diarization)

        Returns:
            A dictionary with the transcript and metadata
        """
        start_time = datetime.now()
        logger.info(f"Starting transcription of {audio_file_path}")

        try:
            # Validate the audio file
            if not os.path.isfile(audio_file_path):
                return create_error_response(f"File not found: {audio_file_path}")

            # Validate and convert the audio format if needed
            audio_array, sampling_rate, duration = process_audio_file(audio_file_path)
            if audio_array is None:
                return create_error_response(f"Failed to process audio file: {audio_file_path}")

            # Detect audio quality issues
            if detect_audio_issues(audio_array, sampling_rate):
                logger.warning("Audio quality issues detected. Results might be affected.")

            # Transcribe with Whisper
            logger.info(f"Running transcription using Whisper {self.transcriber.model_name}")

            # Prepare transcription options
            whisper_options = {
                "language": self.language,
                "task": "transcribe",
                "verbose": False
            }

            # Perform transcription
            result = self.transcriber.transcribe(audio_array, **whisper_options)

            # Process speaker diarization if enabled and requested
            speaker_segments = None
            if self.enable_speaker_diarization and segment_by_speaker and self.diarizer:
                logger.info("Processing speaker diarization")
                speaker_segments = self.diarizer.process_audio(
                    audio_file_path,
                    result["segments"]
                )

            # Format transcript (with timestamps)
            transcript = format_transcript(
                result,
                speaker_segments=speaker_segments
            )

            # Create the response object
            response = {
                "status": "success",
                "metadata": {
                    "file": os.path.basename(audio_file_path),
                    "duration": duration,
                    "model": f"whisper-{self.transcriber.model_name}",
                    "language": self.language,
                    "processing_time": (datetime.now() - start_time).total_seconds(),
                    "include_timestamps": self.include_timestamps
                },
                "transcript": transcript,
                "full_text": result["text"]
            }

            # Save output to file if requested
            if output_file:
                save_output(response, output_format, output_file)

            return response

        except Exception as e:
            logger.error(f"Transcription failed: {str(e)}", exc_info=True)
            return create_error_response(str(e))

    def transcribe_multiple(
            self,
            audio_files: List[str],
            output_dir: Optional[str] = None,
            output_format: str = "json",
            **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Transcribe multiple audio files.

        Args:
            audio_files: List of paths to audio files
            output_dir: Directory to save output files
            output_format: Format for output files
            **kwargs: Additional arguments to pass to transcribe_audio

        Returns:
            List of transcription results
        """
        results = []

        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        for audio_file in audio_files:
            file_name = os.path.basename(audio_file)
            logger.info(f"Processing file: {file_name}")

            # Set output file if output directory is specified
            output_file = None
            if output_dir:
                base_name = os.path.splitext(file_name)[0]
                extension = ".json" if output_format == "json" else f".{output_format}"
                output_file = os.path.join(output_dir, f"{base_name}{extension}")

            # Transcribe the file
            result = self.transcribe_audio(
                audio_file,
                output_format=output_format,
                output_file=output_file,
                **kwargs
            )

            results.append(result)

        return results