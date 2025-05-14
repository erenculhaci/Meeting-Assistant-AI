"""
Configuration constants for the speech recognition package.
"""

# Supported audio formats
SUPPORTED_FORMATS = [".wav", ".mp3", ".ogg", ".flac", ".m4a", ".aac"]

# Available Whisper models
WHISPER_MODELS = ["tiny", "base", "small", "medium", "large", "large-v2", "large-v3"]

# Default Whisper model
DEFAULT_MODEL = "base"

# Default language
DEFAULT_LANGUAGE = "en"

# Default diarization model
DEFAULT_DIARIZATION_MODEL = "pyannote/speaker-diarization"

# Output formats
OUTPUT_FORMATS = ["json", "txt", "srt", "vtt"]