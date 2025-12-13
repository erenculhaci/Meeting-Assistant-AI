import os
import tempfile
from typing import List, Dict, Any, Optional

from pyannote.audio import Pipeline
import torch

from speech_recognition.utils.audio_preprocessing import create_temp_wav_file
from speech_recognition.utils.logging_setup import setup_logger

logger = setup_logger("DiarizationModel")


class SpeakerDiarizer:
    def __init__(
            self,
            model_name: str = "pyannote/speaker-diarization",
            device: Optional[str] = None
    ):
        self.model_name = model_name

        # Auto-detect device if not specified
        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"

        self.device = device
        self.diarizer = None

        # Initialize the diarizer
        self._initialize_diarizer()

    def _initialize_diarizer(self) -> None:
        try:
            # Get token from environment variable
            hf_token = os.environ.get("HF_ACCESS_TOKEN")

            if hf_token:
                self.diarizer = Pipeline.from_pretrained(self.model_name, use_auth_token=hf_token)
                # Move to appropriate device if successfully loaded
                if self.device == "cuda" and torch.cuda.is_available():
                    self.diarizer = self.diarizer.to(torch.device("cuda"))
                return True
            else:
                logger.warning("No Hugging Face token found in environment. Speaker diarization will be disabled.")
                return False
        except Exception as e:
            logger.warning(f"Failed to load speaker diarization model: {e}")
            logger.warning("Speaker diarization will be disabled")
            return False

    def is_available(self) -> bool:
        return self.diarizer is not None

    def process_audio(
            self,
            audio_file_path: str,
            whisper_segments: List[Dict[str, Any]]
    ) -> Optional[List[Dict[str, Any]]]:
        try:
            # Check if diarizer is initialized
            if not self.is_available():
                logger.warning("Speaker diarization requested but diarizer is not initialized")
                return None

            # Convert audio to a temporary WAV file with consistent parameters
            temp_wav_path = create_temp_wav_file(audio_file_path)
            if not temp_wav_path:
                return None

            try:
                # Run diarization on the normalized audio file
                diarization = self.diarizer(temp_wav_path)
            except Exception as e:
                logger.error(f"Audio preprocessing for diarization failed: {str(e)}", exc_info=True)
                # If preprocessing fails, try running directly on the original file as fallback
                try:
                    diarization = self.diarizer(audio_file_path)
                except Exception as inner_e:
                    logger.error(f"Fallback diarization also failed: {str(inner_e)}", exc_info=True)
                    return None
            finally:
                # Clean up temporary file
                if os.path.exists(temp_wav_path):
                    try:
                        os.unlink(temp_wav_path)
                    except:
                        pass

            # Create a dictionary of speaker turns
            speaker_turns = []
            for turn, _, speaker in diarization.itertracks(yield_label=True):
                speaker_turns.append({
                    "speaker": f"Speaker_{speaker.replace('SPEAKER_', '')}",
                    "start": turn.start,
                    "end": turn.end
                })

            # Assign speakers to transcription segments
            speaker_segments = []
            for segment in whisper_segments:
                segment_start = segment["start"]
                segment_end = segment["end"]

                # Find the speaker who speaks the most during this segment
                best_overlap = 0
                best_speaker = None

                for turn in speaker_turns:
                    # Calculate overlap
                    overlap_start = max(segment_start, turn["start"])
                    overlap_end = min(segment_end, turn["end"])
                    overlap = max(0, overlap_end - overlap_start)

                    if overlap > best_overlap:
                        best_overlap = overlap
                        best_speaker = turn["speaker"]

                # If no clear speaker found, use "Unknown"
                if not best_speaker:
                    best_speaker = "Unknown"

                speaker_segments.append({
                    "text": segment["text"],
                    "speaker": best_speaker,
                    "start": segment_start,
                    "end": segment_end
                })

            return speaker_segments

        except Exception as e:
            logger.error(f"Speaker diarization failed: {str(e)}", exc_info=True)
            return None