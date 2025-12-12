"""
LLM-based Speaker Diarization using Groq
=========================================
Analyzes transcript text to identify and assign speakers to each segment.
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional
from groq import Groq

logger = logging.getLogger(__name__)


class LLMDiarizer:
    """
    Uses Groq LLM to analyze transcript and identify speakers.
    """
    
    def __init__(self, model: str = "llama-3.3-70b-versatile"):
        """
        Initialize the LLM diarizer.
        
        Args:
            model: Groq model to use for diarization
        """
        self.model = model
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self) -> bool:
        """Initialize Groq client."""
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            logger.warning("GROQ_API_KEY not found. LLM diarization will be disabled.")
            return False
        
        try:
            self.client = Groq(api_key=api_key)
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Groq client: {e}")
            return False
    
    def diarize_transcript(self, transcript: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Analyze transcript and assign speakers to each segment.
        
        Args:
            transcript: List of transcript segments with text, start, end
            
        Returns:
            Updated transcript with speaker assignments
        """
        if not self.client:
            logger.warning("Groq client not available. Returning transcript without diarization.")
            return transcript
        
        if not transcript:
            return transcript
        
        try:
            # Prepare transcript text for analysis
            transcript_text = self._format_transcript_for_analysis(transcript)
            
            # Get speaker assignments from LLM
            speaker_assignments = self._analyze_speakers(transcript_text, len(transcript))
            
            # Apply speaker assignments to transcript
            updated_transcript = self._apply_speaker_assignments(transcript, speaker_assignments)
            
            return updated_transcript
            
        except Exception as e:
            logger.error(f"Error during LLM diarization: {e}")
            # Return original transcript on error
            return transcript
    
    def _format_transcript_for_analysis(self, transcript: List[Dict[str, Any]]) -> str:
        """Format transcript segments for LLM analysis."""
        lines = []
        for i, seg in enumerate(transcript):
            text = seg.get("text", "").strip()
            start = seg.get("start", 0)
            end = seg.get("end", 0)
            lines.append(f"[{i}] ({start:.1f}s - {end:.1f}s): {text}")
        return "\n".join(lines)
    
    def _analyze_speakers(self, transcript_text: str, segment_count: int) -> Dict[int, str]:
        """
        Use Groq LLM to analyze transcript and identify speakers.
        
        Returns:
            Dictionary mapping segment index to speaker identifier
        """
        system_prompt = """You are an expert at analyzing conversation transcripts and identifying different speakers.

Your task is to analyze the transcript and identify which segments belong to which speaker.

Rules:
1. Identify distinct speakers based on context, speaking patterns, and conversation flow
2. Assign each speaker a consistent identifier (Speaker_A, Speaker_B, Speaker_C, etc.)
3. If names are mentioned in the conversation (e.g., "Thanks John", "Hi Sarah"), use those actual names instead of Speaker_X
4. Pay attention to:
   - Turn-taking patterns (responses to questions)
   - Different speaking styles or vocabulary
   - Context clues about who is speaking
   - Direct addresses or mentions of names
5. Be consistent - the same speaker should always have the same identifier

Output format:
Return ONLY a JSON object mapping segment indices to speaker identifiers.
Example: {"0": "John", "1": "Sarah", "2": "John", "3": "Mike"}

Do not include any explanation, just the JSON object."""

        user_prompt = f"""Analyze this transcript and identify the speaker for each segment:

{transcript_text}

Return a JSON object mapping each segment index (0 to {segment_count - 1}) to a speaker identifier.
Use actual names if mentioned in the conversation, otherwise use Speaker_A, Speaker_B, etc."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,  # Low temperature for consistent results
                max_tokens=4096
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # Parse JSON response
            # Handle potential markdown code blocks
            if result_text.startswith("```"):
                result_text = result_text.split("```")[1]
                if result_text.startswith("json"):
                    result_text = result_text[4:]
                result_text = result_text.strip()
            
            speaker_map = json.loads(result_text)
            
            # Convert string keys to integers
            return {int(k): v for k, v in speaker_map.items()}
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            logger.debug(f"Response was: {result_text}")
            return {}
        except Exception as e:
            logger.error(f"Error calling Groq API: {e}")
            return {}
    
    def _apply_speaker_assignments(
        self, 
        transcript: List[Dict[str, Any]], 
        assignments: Dict[int, str]
    ) -> List[Dict[str, Any]]:
        """Apply speaker assignments to transcript segments."""
        updated = []
        for i, seg in enumerate(transcript):
            new_seg = seg.copy()
            if i in assignments:
                new_seg["speaker"] = assignments[i]
            else:
                # Default speaker if not assigned
                new_seg["speaker"] = f"Speaker_{i % 10}"
            updated.append(new_seg)
        return updated
    
    def get_unique_speakers(self, transcript: List[Dict[str, Any]]) -> List[str]:
        """Get list of unique speakers from transcript."""
        speakers = set()
        for seg in transcript:
            speaker = seg.get("speaker", "Unknown")
            speakers.add(speaker)
        return sorted(list(speakers))
