"""
Person extraction utilities for identifying people in meeting transcripts.
"""

import re
from typing import List, Dict, Set, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

# Try to import spacy for advanced NER
try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    logger.warning("spacy not installed. Advanced person extraction will be limited.")


class PersonExtractor:
    """Extract and normalize person names from meeting transcripts."""
    
    def __init__(self):
        """Initialize the person extractor."""
        self.common_names = {
            # Male names
            'alex', 'andrew', 'adam', 'aaron', 'anthony', 'austin',
            'ben', 'bob', 'brian', 'brandon', 'brad', 'blake',
            'chris', 'christian', 'carlos', 'connor', 'cole', 'caleb',
            'dan', 'daniel', 'david', 'derek', 'drew', 'dylan',
            'eric', 'ethan', 'evan', 'elijah',
            'frank', 'fred',
            'greg', 'grant', 'garrett', 'george',
            'henry', 'hunter',
            'ian', 'isaac',
            'jack', 'james', 'jason', 'jeff', 'john', 'jordan', 'josh', 'justin', 'jacob',
            'kevin', 'kyle', 'keith', 'kenneth',
            'luke', 'logan', 'liam', 'lucas',
            'mark', 'matt', 'michael', 'mike', 'max', 'mason', 'matthew',
            'nick', 'noah', 'nathan', 'nathaniel',
            'owen', 'oliver',
            'paul', 'peter', 'patrick',
            'robert', 'ryan', 'richard', 'raymond',
            'sam', 'scott', 'steve', 'sean', 'seth', 'sebastian',
            'tim', 'tom', 'tyler', 'travis', 'troy', 'taylor',
            'victor', 'vincent',
            'will', 'william', 'wyatt',
            'zachary', 'zach',
            
            # Female names
            'abby', 'abigail', 'amanda', 'amy', 'anna', 'andrea', 'angela', 'alice', 'ashley', 'alexis',
            'barbara', 'betty', 'brenda', 'brittany', 'brooke',
            'carol', 'catherine', 'christine', 'christina', 'chloe', 'claire',
            'deborah', 'debbie', 'diana', 'donna',
            'elizabeth', 'emily', 'emma', 'erin', 'evelyn',
            'grace', 'gabrielle',
            'hannah', 'helen', 'heather',
            'isabel', 'isabella',
            'jennifer', 'jessica', 'julia', 'julie', 'janet', 'jane',
            'karen', 'kate', 'katie', 'katherine', 'kimberly', 'kim', 'kelly',
            'laura', 'lauren', 'linda', 'lisa', 'lucy',
            'mary', 'maria', 'margaret', 'megan', 'melissa', 'michelle', 'maya',
            'nancy', 'natalie', 'nicole', 'nina',
            'olivia',
            'pamela', 'patricia', 'rachel', 'rebecca',
            'sandra', 'sarah', 'samantha', 'shannon', 'sophia', 'stephanie', 'susan', 'sara',
            'tiffany', 'teresa',
            'victoria', 'vanessa',
            'wendy',
            'zoe',
            
            # Unisex names
            'alex', 'jordan', 'taylor', 'morgan', 'casey', 'riley', 'jamie', 'drew',
            'pat', 'charlie', 'skyler', 'avery', 'harper', 'parker', 'quinn', 'rowan'
        }
        
        # Map speaker IDs to actual names if mentioned
        self.speaker_name_map: Dict[str, str] = {}
        
        # Load spacy model if available
        self.nlp = None
        if SPACY_AVAILABLE:
            try:
                # Try to load small English model
                self.nlp = spacy.load('en_core_web_sm')
                logger.info("Spacy NER enabled for person extraction")
            except OSError:
                logger.warning("Spacy model 'en_core_web_sm' not found. Install with: python -m spacy download en_core_web_sm")
                self.nlp = None

    
    def extract_persons(self, transcript_data: Dict) -> Dict[str, str]:
        """
        Extract person names and map them to speaker IDs.
        
        Args:
            transcript_data: Transcript data with segments
            
        Returns:
            Dictionary mapping speaker IDs to names
        """
        transcript_segments = transcript_data.get('transcript', [])
        
        # Try spacy-based extraction first
        if self.nlp:
            self._extract_with_spacy(transcript_segments)
        
        # Fallback/supplement with pattern-based extraction
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
    
    def _extract_with_spacy(self, segments: List[Dict]) -> None:
        """Extract person names using spacy NER."""
        for i, segment in enumerate(segments):
            text = segment.get('text', '')
            speaker = segment.get('speaker', '')
            
            # Process with spacy
            doc = self.nlp(text)
            
            # Extract PERSON entities
            for ent in doc.ents:
                if ent.label_ == 'PERSON':
                    name = ent.text.strip()
                    
                    # Skip if it's a common word or too short
                    if len(name) < 3 or name.lower() in ['speaker', 'everyone', 'someone', 'anyone']:
                        continue
                    
                    # Check if this might be referring to a speaker
                    # Look ahead for responses
                    for j in range(i + 1, min(i + 3, len(segments))):
                        next_segment = segments[j]
                        next_speaker = next_segment.get('speaker', '')
                        next_text = next_segment.get('text', '').lower()
                        
                        # Check for affirmative responses
                        if re.search(r'\b(yes|yeah|sure|okay|will do|got it)\b', next_text):
                            if next_speaker not in self.speaker_name_map:
                                self.speaker_name_map[next_speaker] = name
                            break
    
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
        Extract potential assignees from a single text segment with comprehensive patterns.
        
        Args:
            text: Text to analyze
            context_segments: Surrounding segments for context
            
        Returns:
            List of potential assignees (names or speaker IDs)
        """
        assignees = []
        
        # Pattern 1: Direct assignment "Name, you will/should/need to..."
        pattern1 = r'\b([A-Z][a-z]+),?\s+(?:you\s+)?(?:will|should|need to|have to|must|can you|could you|please|would you)'
        matches = re.finditer(pattern1, text)
        for match in matches:
            name = match.group(1)
            if name.lower() in self.common_names or len(name) >= 3:
                assignees.append(name)
        
        # Pattern 2: "Name is/will be responsible for..."
        pattern2 = r'\b([A-Z][a-z]+)\s+(?:is|will be|is going to be|has been)\s+(?:responsible for|in charge of|handling|leading|managing)'
        matches = re.finditer(pattern2, text)
        for match in matches:
            name = match.group(1)
            if name.lower() in self.common_names or len(name) >= 3:
                assignees.append(name)
        
        # Pattern 3: "Let's have Name..." or "Let's have Name and Name..."
        pattern3 = r"\blet'?s\s+have\s+([A-Z][a-z]+)(?:\s+and\s+([A-Z][a-z]+))?"
        matches = re.finditer(pattern3, text, re.IGNORECASE)
        for match in matches:
            name = match.group(1)
            if name.lower() in self.common_names or len(name) >= 3:
                assignees.append(name)
            if match.group(2):
                name2 = match.group(2)
                if name2.lower() in self.common_names or len(name2) >= 3:
                    assignees.append(name2)
        
        # Pattern 4: "I want Name to..."
        pattern4 = r'\bI\s+(?:want|need|would like|\'d like)\s+([A-Z][a-z]+)\s+to\b'
        matches = re.finditer(pattern4, text)
        for match in matches:
            name = match.group(1)
            if name.lower() in self.common_names or len(name) >= 3:
                assignees.append(name)
        
        # Pattern 5: "Name will/should/can..."
        pattern5 = r'\b([A-Z][a-z]+)\s+(?:will|should|can|could|would)\s+(?:handle|take care of|work on|do|complete|finish|deliver)'
        matches = re.finditer(pattern5, text)
        for match in matches:
            name = match.group(1)
            if name.lower() in self.common_names or len(name) >= 3:
                assignees.append(name)
        
        # Pattern 6: "Assign/Delegate Name to..." or "Assigned to Name" or "Assign this to Name and Name"
        pattern6 = r'\b(?:assign|assigned|delegate|delegated)(?:\s+this)?\s+to\s+([A-Z][a-z]+)(?:\s+and\s+([A-Z][a-z]+))?'
        matches = re.finditer(pattern6, text, re.IGNORECASE)
        for match in matches:
            name = match.group(1)
            if name.lower() in self.common_names or len(name) >= 3:
                assignees.append(name)
            if match.group(2):
                name2 = match.group(2)
                if name2.lower() in self.common_names or len(name2) >= 3:
                    assignees.append(name2)
        
        # Pattern 7: Collaborative assignments "Name and Name" or "Name & Name"
        # First check for "Name and Name, you/both/all..." pattern
        collab_pattern1 = r'\b([A-Z][a-z]+)\s+and\s+([A-Z][a-z]+),?\s+(?:you\s+)?(?:both|all|will|should|can)'
        matches = re.finditer(collab_pattern1, text)
        for match in matches:
            name1 = match.group(1)
            name2 = match.group(2)
            if name1.lower() in self.common_names or len(name1) >= 3:
                assignees.append(name1)
            if name2.lower() in self.common_names or len(name2) >= 3:
                assignees.append(name2)
        
        # Then check for "Name & Name" pattern
        collab_pattern2 = r'\b([A-Z][a-z]+)\s+&\s+([A-Z][a-z]+)'
        matches = re.finditer(collab_pattern2, text)
        for match in matches:
            name1 = match.group(1)
            name2 = match.group(2)
            if name1.lower() in self.common_names or len(name1) >= 3:
                assignees.append(name1)
            if name2.lower() in self.common_names or len(name2) >= 3:
                assignees.append(name2)
        
        # Pattern 8: "Name, Name, and Name" (list of assignees)
        list_pattern = r'\b([A-Z][a-z]+)(?:,\s+([A-Z][a-z]+))*(?:,?\s+and\s+([A-Z][a-z]+))?\s+(?:will|should|can|to|all)'
        matches = re.finditer(list_pattern, text)
        for match in matches:
            for i in range(1, 4):
                if match.group(i):
                    name = match.group(i)
                    if name.lower() in self.common_names or len(name) >= 3:
                        assignees.append(name)
        
        # Pattern 9: "I'll/I will..." (speaker is assignee)
        if re.search(r"\b(?:I'll|I will|I'm going to|I can|I should|I'm gonna|I'll handle|Let me)\b", text):
            assignees.append('SPEAKER')  # Special marker for current speaker
        
        # Pattern 10: "We'll" when in response context (speaker included)
        if re.search(r"\b(?:We'll|We will|We can|We should)\b", text):
            if context_segments:
                # Check if this is a response to an assignment
                assignees.append('SPEAKER')
        
        # Pattern 11: Third person assignment "Have Name do..." or "Have Name and Name..."
        pattern11 = r'\bhave\s+([A-Z][a-z]+)(?:\s+and\s+([A-Z][a-z]+))?\s+(?:do|work on|handle|take care of|complete)'
        matches = re.finditer(pattern11, text, re.IGNORECASE)
        for match in matches:
            name = match.group(1)
            if name.lower() in self.common_names or len(name) >= 3:
                assignees.append(name)
            if match.group(2):
                name2 = match.group(2)
                if name2.lower() in self.common_names or len(name2) >= 3:
                    assignees.append(name2)
        
        # Pattern 12: "Name's task is..." or "Name's responsibility"
        pattern12 = r"\b([A-Z][a-z]+)'s\s+(?:task|responsibility|job|role)\s+(?:is|will be)"
        matches = re.finditer(pattern12, text)
        for match in matches:
            name = match.group(1)
            if name.lower() in self.common_names or len(name) >= 3:
                assignees.append(name)
        
        # Third person mentions (existing method)
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
