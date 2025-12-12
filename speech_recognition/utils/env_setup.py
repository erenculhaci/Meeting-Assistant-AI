"""
Environment setup for the speech recognition package.
"""

import os
import logging
from dotenv import load_dotenv


def setup_environment():
    """
    Load environment variables from .env file and set up necessary configurations.

    Returns:
        True if the environment was successfully set up, False otherwise
    """
    # Try to locate .env file in parent directory of the package
    try:
        # Get the speech_recognition package directory
        package_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        env_file = os.path.join(package_dir, ".env")

        # Try to load .env file
        loaded = load_dotenv(env_file)

        if loaded:
            logging.info(f"Environment variables loaded from {env_file}")
        else:
            logging.warning(f"No .env file found at {env_file}")

        # Check for required environment variables
        hf_token = os.environ.get("HF_ACCESS_TOKEN")
        if not hf_token:
            logging.warning("HF_ACCESS_TOKEN environment variable not set. Speaker diarization may not work.")

        return True

    except Exception as e:
        logging.error(f"Failed to set up environment: {str(e)}")
        return False