"""
Audio/Video Transcription Module
Supports: MP3, WAV, MP4, M4A, WEBM, OGG, FLAC and more
Output formats: JSON (with timestamps & speakers), SRT (subtitles), TXT (plain text), VTT (web subtitles)
"""

from .transcriber import Transcriber
from .formatters import JSONFormatter, SRTFormatter, TXTFormatter, VTTFormatter

__version__ = "1.0.0"
__all__ = ["Transcriber", "JSONFormatter", "SRTFormatter", "TXTFormatter", "VTTFormatter"]
