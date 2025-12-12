"""
Whisper model implementation for speech recognition.
"""

import torch
import whisper
from typing import Dict, Any, Optional

from speech_recognition.core.config import WHISPER_MODELS
from speech_recognition.utils.logging_setup import setup_logger

logger = setup_logger("WhisperModel")


class WhisperTranscriber:
    """
    Wrapper for the Whisper ASR model.
    """

    def __init__(
            self,
            model_name: str = "base",
            device: Optional[str] = None,
            language: str = "en",
    ):
        """
        Initialize the Whisper transcriber.

        Args:
            model_name: Whisper model size
            device: Device to run inference on ("cpu", "cuda", or None for auto-detection)
            language: Language code for transcription
        """
        # Auto-detect device if not specified
        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"

        self.device = device
        self.language = language

        # Validate model name
        if model_name not in WHISPER_MODELS:
            logger.warning(f"Invalid Whisper model: {model_name}. Using 'base' instead.")
            model_name = "base"

        self.model_name = model_name

        logger.info(f"Loading Whisper {model_name} model on {device}")
        try:
            self.model = whisper.load_model(model_name, device=device)
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}", exc_info=True)
            raise RuntimeError(f"Failed to initialize Whisper model: {e}")

    def transcribe(self, audio_array, **options) -> Dict[str, Any]:
        """
        Transcribe audio using Whisper.

        Args:
            audio_array: Audio data as numpy array
            **options: Additional options for Whisper transcription

        Returns:
            Transcription result dictionary
        """
        # Set default options if not provided
        if "language" not in options:
            options["language"] = self.language
        if "task" not in options:
            options["task"] = "transcribe"
        if "verbose" not in options:
            options["verbose"] = False

        # Perform transcription
        return self.model.transcribe(audio_array, **options)