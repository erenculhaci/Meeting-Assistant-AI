"""
Configuration constants for the speech recognition package.
"""

# Supported audio formats
SUPPORTED_FORMATS = [".wav", ".mp3", ".ogg", ".flac", ".m4a", ".aac", ".mp4", ".webm", ".mkv", ".avi", ".mov"]

# tiny: ~1GB RAM, fastest
# base: ~1GB RAM, good balance
# small: ~2GB RAM, better accuracy
# medium: ~5GB RAM, high accuracy
# large-v3: ~10GB RAM, best accuracy
WHISPER_MODELS = ["tiny", "base", "small", "medium", "large", "large-v2", "large-v3"]

# Default Whisper model - "base" is fast and accurate enough for most cases
DEFAULT_MODEL = "base"

# Default language (None = auto-detect, "tr" for Turkish, "en" for English)
DEFAULT_LANGUAGE = None

# Default diarization model - using the latest 3.1 version
DEFAULT_DIARIZATION_MODEL = "pyannote/speaker-diarization-3.1"

# Output formats
OUTPUT_FORMATS = ["json", "txt", "srt", "vtt"]