"""
Configuration for Meeting Assistant AI
======================================
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).parent.parent.parent / ".env")

# Directories
UPLOAD_DIR = Path(__file__).parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

CONFIG_FILE = Path(__file__).parent / "config.json"

# CORS settings
CORS_ORIGINS = ["http://localhost:3000", "http://localhost:5173"]

# Allowed file extensions for upload
ALLOWED_EXTENSIONS = {'.mp3', '.mp4', '.wav', '.m4a', '.webm', '.ogg', '.flac'}

# Whisper model configuration
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")
