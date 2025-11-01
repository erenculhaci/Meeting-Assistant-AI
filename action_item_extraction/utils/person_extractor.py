"""
Person extraction utilities for identifying people in meeting transcripts.
"""

import re
from typing import List, Dict, Set, Tuple
import logging

logger = logging.getLogger(__name__)


class PersonExtractor:
    """Extract and normalize person names from meeting transcripts."""
    
    def __init__(self):
        """Initialize the person extractor."""
        self.common_names = {
            'sarah', 'tom', 'maya', 'john', 'mike', 'david', 'james', 'robert',
            'mary', 'lisa', 'anna', 'emily', 'michael', 'chris', 'alex', 'sam',
            'jordan', 'taylor', 'morgan', 'casey', 'riley', 'jamie', 'drew',
            'ben', 'dan', 'joe', 'bob', 'jim', 'tim', 'kim', 'pat', 'max'
        }
        
        # Map speaker IDs to actual names if mentioned
        self.speaker_name_map: Dict[str, str] = {}
    
    def extract_persons(self, transcript_data: Dict) -> Dict[str, str]:
        """
        Extract person names and map them to speaker IDs.
        
        Args:
            transcript_data: Transcript data with segments
            
        Returns:
            Dictionary mapping speaker IDs to names
        """
        transcript_segments = transcript_data.get('transcript', [])
        
        # Try to find name mentions in the conversation
        for i, segment in enumerate(transcript_segments):
            text = segment.get('text', '')
            speaker = segment.get('speaker', 'Unknown')
            
            # Pattern 1: Direct address "Sarah, can you..."
            names = self._extract_direct_address(text)
            
            # Pattern 2: Third person "Let's have Tom handle..."
            names.extend(self._extract_third_person_mention(text))
            
            # Try to map these names to speakers based on context
            self._map_names_to_speakers(names, transcript_segments, i)
        
        return self.speaker_name_map
    
    def _extract_direct_address(self, text: str) -> List[str]:
        """Extract names from direct address patterns."""
        names = []
        
        # Pattern: "Name, ..." at the beginning
        match = re.match(r'^([A-Z][a-z]+),\s+', text)
        if match:
            name = match.group(1)
            if name.lower() in self.common_names or len(name) >= 3:
                names.append(name)
        
        # Pattern: "... Name?" questions directed at someone
        match = re.search(r',\s+([A-Z][a-z]+)\?', text)
        if match:
            name = match.group(1)
            if name.lower() in self.common_names or len(name) >= 3:
                names.append(name)
        
        return names
    
    def _extract_third_person_mention(self, text: str) -> List[str]:
        """Extract names mentioned in third person."""
        names = []
        
        # Patterns: "have Tom/Sarah/etc do...", "Tom will...", "Sarah can..."
        patterns = [
            r'\b(?:have|let|ask|tell)\s+([A-Z][a-z]+)\s+(?:do|handle|take|lead|work)',
            r'\b([A-Z][a-z]+)\s+(?:will|should|can|could|would|needs? to|has to)',
            r'\b([A-Z][a-z]+)\'s\s+(?:going to|gonna|responsible|task|job)',
            r'\b(?:assign|assigned|give|gave)\s+(?:to\s+)?([A-Z][a-z]+)',
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                name = match.group(1)
                # Filter out common words that might match
                if name.lower() not in ['speaker', 'team', 'group', 'everyone', 'someone']:
                    if name.lower() in self.common_names or len(name) >= 3:
                        names.append(name)
        
        return names
    
    def _map_names_to_speakers(self, names: List[str], segments: List[Dict], current_idx: int):
        """Map extracted names to speaker IDs based on context."""
        if not names:
            return
        
        # Look ahead to see who responds (likely the person being addressed)
        for name in names:
            # Check next few segments for responses
            for i in range(current_idx + 1, min(current_idx + 4, len(segments))):
                next_segment = segments[i]
                next_speaker = next_segment.get('speaker', '')
                next_text = next_segment.get('text', '').lower()
                
                # Check for affirmative responses
                affirmative_patterns = [
                    r'\b(yes|yeah|sure|okay|ok|got it|will do|sounds good|happy to|understood|copy that|perfect|great|alright)\b',
                ]
                
                for pattern in affirmative_patterns:
                    if re.search(pattern, next_text):
                        # This speaker is likely the person being addressed
                        if next_speaker not in self.speaker_name_map:
                            self.speaker_name_map[next_speaker] = name
                        break
    
    def get_person_for_speaker(self, speaker_id: str) -> str:
        """
        Get the person name for a speaker ID.
        
        Args:
            speaker_id: Speaker ID (e.g., "Speaker_01")
            
        Returns:
            Person name or speaker ID if not found
        """
        return self.speaker_name_map.get(speaker_id, speaker_id)
    
    def extract_assignee_from_text(self, text: str, context_segments: List[Dict] = None) -> List[str]:
        """
        Extract potential assignees from a single text segment.
        
        Args:
            text: Text to analyze
            context_segments: Surrounding segments for context
            
        Returns:
            List of potential assignees (names or speaker IDs)
        """
        assignees = []
        
        # Pattern 1: Explicit assignment "Sarah, you will/should/need to..."
        pattern1 = r'\b([A-Z][a-z]+),?\s+(?:you\s+)?(?:will|should|need to|have to|can you|could you|please)'
        matches = re.finditer(pattern1, text)
        for match in matches:
            name = match.group(1)
            if name.lower() in self.common_names or len(name) >= 3:
                assignees.append(name)
        
        # Pattern 2: "I'll/I will..." (speaker is assignee)
        if re.search(r"\b(?:I'll|I will|I'm going to|I can|I should)\b", text):
            assignees.append('SPEAKER')  # Special marker for current speaker
        
        # Pattern 3: Third person assignment
        third_person_names = self._extract_third_person_mention(text)
        assignees.extend(third_person_names)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_assignees = []
        for assignee in assignees:
            if assignee not in seen:
                seen.add(assignee)
                unique_assignees.append(assignee)
        
        return unique_assignees
