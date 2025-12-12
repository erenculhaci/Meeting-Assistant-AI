"""
Speech Recognition package for transcribing audio files.
"""

import os
from speech_recognition.utils.env_setup import setup_environment

__version__ = "1.0.0"

# Set up environment variables when package is imported
setup_environment()

# Export main classes and functions for easy access
from speech_recognition.core.meeting_transcriber import MeetingTranscriber
from speech_recognition.transcriber import transcribe_meeting

__all__ = ['MeetingTranscriber', 'transcribe_meeting']