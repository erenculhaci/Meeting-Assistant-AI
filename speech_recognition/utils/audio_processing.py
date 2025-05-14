"""
Audio processing utilities for the speech recognition package.
"""

import os
import tempfile
import numpy as np
import librosa
from pydub import AudioSegment
from typing import Optional, Tuple

from speech_recognition.core.config import SUPPORTED_FORMATS
from speech_recognition.utils.logging_setup import setup_logger

logger = setup_logger("AudioProcessing")


def process_audio_file(audio_file_path: str) -> Tuple[Optional[np.ndarray], int, float]:
    """
    Process the audio file and convert it to the required format.

    Args:
        audio_file_path: Path to the audio file

    Returns:
        Tuple of (audio_array, sampling_rate, duration) or (None, None, None) on failure
    """
    file_ext = os.path.splitext(audio_file_path)[1].lower()

    if file_ext not in SUPPORTED_FORMATS:
        logger.warning(f"Unsupported audio format: {file_ext}")
        logger.info(f"Supported formats: {', '.join(SUPPORTED_FORMATS)}")
        return None, None, None

    try:
        # If wav format, load directly with librosa
        if file_ext == ".wav":
            # Whisper expects 16kHz mono audio
            audio_array, sampling_rate = librosa.load(audio_file_path, sr=16000, mono=True)
            duration = librosa.get_duration(y=audio_array, sr=sampling_rate)
            return audio_array, sampling_rate, duration

        # For other formats, convert to wav using pydub first
        logger.info(f"Converting {file_ext} to WAV format")
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_wav:
            audio = AudioSegment.from_file(audio_file_path)
            # Convert to mono and set sample rate to 16kHz for Whisper
            audio = audio.set_channels(1).set_frame_rate(16000)
            audio.export(temp_wav.name, format="wav")

            # Load the converted WAV file
            audio_array, sampling_rate = librosa.load(temp_wav.name, sr=16000, mono=True)
            duration = len(audio) / 1000.0  # pydub duration is in milliseconds

        return audio_array, sampling_rate, duration

    except Exception as e:
        logger.error(f"Error processing audio file: {str(e)}", exc_info=True)
        return None, None, None


def detect_audio_issues(audio_array: np.ndarray, sampling_rate: int) -> bool:
    """
    Detect common audio quality issues.

    Args:
        audio_array: Audio data as numpy array
        sampling_rate: Audio sampling rate

    Returns:
        True if issues were detected, False otherwise
    """
    issues_detected = False

    # Check for very low volume
    rms = np.sqrt(np.mean(audio_array ** 2))
    if rms < 0.01:
        logger.warning("Low audio volume detected")
        issues_detected = True

    # Check for clipping
    if np.max(np.abs(audio_array)) > 0.95:
        logger.warning("Audio clipping detected")
        issues_detected = True

    # Check for very short duration
    duration = len(audio_array) / sampling_rate
    if duration < 1.0:
        logger.warning(f"Very short audio ({duration:.2f}s)")
        issues_detected = True

    return issues_detected


def create_temp_wav_file(audio_file_path: str) -> str:
    """
    Create a temporary WAV file from the provided audio file.

    Args:
        audio_file_path: Path to the audio file

    Returns:
        Path to the temporary WAV file, or None on failure
    """
    try:
        temp_wav = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        temp_wav_path = temp_wav.name
        temp_wav.close()

        # Load and convert audio using pydub
        audio = AudioSegment.from_file(audio_file_path)
        # Convert to mono and set sample rate to 16kHz for compatibility
        audio = audio.set_channels(1).set_frame_rate(16000)
        audio.export(temp_wav_path, format="wav")

        return temp_wav_path

    except Exception as e:
        logger.error(f"Failed to create temporary WAV file: {str(e)}", exc_info=True)
        if os.path.exists(temp_wav_path):
            try:
                os.unlink(temp_wav_path)
            except:
                pass
        return None