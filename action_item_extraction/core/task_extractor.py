"""
Core task extraction engine using NLP and pattern matching.
"""

import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

from action_item_extraction.utils.date_parser import DateParser
from action_item_extraction.utils.person_extractor import PersonExtractor

logger = logging.getLogger(__name__)


class TaskExtractor:
    """
    Advanced task extraction from meeting transcripts.
    
    Handles:
    - Explicit task assignments
    - Implicit tasks and commitments
    - Deadline extraction (explicit and relative dates)
    - Person/speaker assignment
    - Task prioritization
    - Context-aware extraction
    """
    
    def __init__(self, reference_date: Optional[datetime] = None):
        """
        Initialize the task extractor.
        
        Args:
            reference_date: Reference date for date parsing (default: today)
        """
        self.date_parser = DateParser(reference_date)
        self.person_extractor = PersonExtractor()
        
        # Task indicator patterns (verb phrases that indicate tasks)
        self.task_patterns = [
            # Explicit assignments
            (r'\b(?:need to|needs to|needed to)\s+(.{5,150})', 'high', 'explicit'),
            (r'\b(?:should|ought to)\s+(.{5,150})', 'medium', 'explicit'),
            (r'\b(?:will|\'ll)\s+(.{5,150})', 'medium', 'commitment'),
            (r'\b(?:going to|gonna)\s+(.{5,150})', 'medium', 'commitment'),
            (r'\b(?:have to|has to|had to|must|required to)\s+(.{5,150})', 'high', 'explicit'),
            
            # Action directives
            (r'\b(?:please|can you|could you|would you)\s+(.{5,150})', 'high', 'request'),
            (r'\b(?:let\'s|let us)\s+(.{5,150})', 'medium', 'collaborative'),
            
            # Specific action verbs
            (r'\b(?:complete|finish|deliver|submit|send|provide|create|build|develop|implement|review|check|verify|analyze|prepare|organize|schedule|coordinate|handle|lead|work on|take care of)\s+(.{5,150})', 'medium', 'action'),
            
            # Responsibility assignment
            (r'\b(?:responsible for|in charge of|assigned to|tasked with)\s+(.{5,150})', 'high', 'assignment'),
            
            # Future commitments
            (r'\b(?:I\'ll|I will|I\'m going to|I can|I should)\s+(.{5,150})', 'medium', 'self_commitment'),
        ]
        
        # Context indicators for task boundaries
        self.task_end_indicators = [
            r'\.\s+(?:[A-Z]|$)',  # End of sentence
            r'\?',  # Question mark
            r'\!',  # Exclamation
            r'\s+(?:and|but|or|so|because|if|when|where|who|what|how)\s+',  # Conjunctions
        ]
    
    def extract_tasks(self, transcript_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract all tasks from the transcript.
        
        Args:
            transcript_data: Transcript data in JSON format
            
        Returns:
            List of task dictionaries with metadata
        """
        logger.info("Starting task extraction")
        
        # First, map speakers to names
        self.person_extractor.extract_persons(transcript_data)
        
        transcript_segments = transcript_data.get('transcript', [])
        tasks = []
        
        # Process each segment
        for i, segment in enumerate(transcript_segments):
            text = segment.get('text', '')
            speaker = segment.get('speaker', 'Unknown')
            
            # Skip very short or irrelevant segments
            if len(text.strip()) < 10:
                continue
            
            # Skip greetings and closings
            if self._is_greeting_or_closing(text):
                continue
            
            # Extract tasks from this segment
            segment_tasks = self._extract_tasks_from_segment(
                text, speaker, i, transcript_segments
            )
            
            tasks.extend(segment_tasks)
        
        # Post-process: deduplicate and enhance tasks
        tasks = self._deduplicate_tasks(tasks)
        tasks = self._enhance_tasks(tasks, transcript_data)
        
        logger.info(f"Extracted {len(tasks)} tasks")
        
        return tasks
    
    def _extract_tasks_from_segment(
        self, text: str, speaker: str, idx: int, all_segments: List[Dict]
    ) -> List[Dict[str, Any]]:
        """Extract tasks from a single segment with context."""
        tasks = []
        
        # Try each pattern
        for pattern, priority, task_type in self.task_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            
            for match in matches:
                task_description = match.group(1).strip()
                
                # Clean up the task description
                task_description = self._clean_task_description(task_description)
                
                if not task_description or len(task_description) < 10:
                    continue
                
                # Extract dates from the task description and context
                dates = self._extract_task_dates(text, all_segments, idx)
                
                # Extract assignee
                assignee = self._extract_assignee(text, speaker, task_type, all_segments, idx)
                
                # Create task object
                task = {
                    'description': task_description,
                    'assignee': assignee,
                    'speaker': speaker,
                    'priority': priority,
                    'type': task_type,
                    'start_date': dates.get('start'),
                    'due_date': dates.get('due'),
                    'mentioned_dates': dates.get('all_dates', []),
                    'source_text': text,
                    'confidence': self._calculate_confidence(task_description, dates, assignee)
                }
                
                tasks.append(task)
        
        return tasks
    
    def _clean_task_description(self, description: str) -> str:
        """Clean and normalize task description."""
        # Remove trailing punctuation and conjunctions
        for end_pattern in self.task_end_indicators:
            match = re.search(end_pattern, description)
            if match:
                description = description[:match.start()].strip()
                break
        
        # Remove common filler phrases
        description = re.sub(r'\b(?:you know|I mean|like|um|uh|basically|actually)\b', '', description, flags=re.IGNORECASE)
        
        # Clean up whitespace
        description = re.sub(r'\s+', ' ', description).strip()
        
        # Remove trailing prepositions and articles
        description = re.sub(r'\s+(?:a|an|the|to|for|with|by|on|in|at)$', '', description, flags=re.IGNORECASE)
        
        return description
    
    def _extract_task_dates(
        self, text: str, all_segments: List[Dict], current_idx: int
    ) -> Dict[str, Any]:
        """Extract dates related to a task from text and context."""
        dates = {}
        all_found_dates = []
        
        # Extract from current segment
        segment_dates = self.date_parser.extract_dates(text)
        all_found_dates.extend(segment_dates)
        
        # Look at previous and next segments for context
        context_range = 2
        for i in range(max(0, current_idx - context_range), 
                      min(len(all_segments), current_idx + context_range + 1)):
            if i != current_idx:
                context_text = all_segments[i].get('text', '')
                context_dates = self.date_parser.extract_dates(context_text)
                all_found_dates.extend(context_dates)
        
        # Process found dates
        if all_found_dates:
            # Sort by date
            sorted_dates = sorted(set([d[1] for d in all_found_dates]))
            
            # Heuristic: earliest date is likely start, latest is due date
            if len(sorted_dates) == 1:
                dates['due'] = sorted_dates[0]
                dates['start'] = None
            elif len(sorted_dates) >= 2:
                dates['start'] = sorted_dates[0]
                dates['due'] = sorted_dates[-1]
            
            dates['all_dates'] = [d[1].strftime('%Y-%m-%d') for d in all_found_dates]
        else:
            dates['start'] = None
            dates['due'] = None
            dates['all_dates'] = []
        
        return dates
    
    def _extract_assignee(
        self, text: str, speaker: str, task_type: str, 
        all_segments: List[Dict], idx: int
    ) -> str:
        """Determine who is assigned to the task."""
        # Try to extract from text
        assignees = self.person_extractor.extract_assignee_from_text(text)
        
        if assignees:
            # If 'SPEAKER' marker found, use the current speaker
            if 'SPEAKER' in assignees:
                return self.person_extractor.get_person_for_speaker(speaker)
            
            # Otherwise, use the first mentioned name
            first_assignee = assignees[0]
            
            # Try to map name to a speaker
            for speaker_id, name in self.person_extractor.speaker_name_map.items():
                if name.lower() == first_assignee.lower():
                    return name
            
            return first_assignee
        
        # Fallback: if it's a self-commitment type, assign to speaker
        if task_type == 'self_commitment':
            return self.person_extractor.get_person_for_speaker(speaker)
        
        # Look at next segment for responses (implicit assignment)
        if idx + 1 < len(all_segments):
            next_segment = all_segments[idx + 1]
            next_text = next_segment.get('text', '').lower()
            next_speaker = next_segment.get('speaker', '')
            
            # Check for acceptance responses
            if re.search(r'\b(yes|yeah|sure|okay|ok|got it|will do|sounds good|happy to|understood|i\'ll|i will)\b', next_text):
                return self.person_extractor.get_person_for_speaker(next_speaker)
        
        # Default: unassigned
        return 'Unassigned'
    
    def _calculate_confidence(
        self, description: str, dates: Dict, assignee: str
    ) -> float:
        """Calculate confidence score for the extracted task."""
        confidence = 0.5  # Base confidence
        
        # Has clear description
        if len(description) > 20:
            confidence += 0.1
        
        # Has assignee
        if assignee and assignee != 'Unassigned':
            confidence += 0.2
        
        # Has deadline
        if dates.get('due'):
            confidence += 0.15
        
        # Has start date
        if dates.get('start'):
            confidence += 0.05
        
        return min(confidence, 1.0)
    
    def _is_greeting_or_closing(self, text: str) -> bool:
        """Check if text is a greeting or closing."""
        text_lower = text.lower().strip()
        
        greetings = [
            r'^(good\s+)?(morning|afternoon|evening|night)',
            r'^(hi|hey|hello|howdy)',
            r'^(bye|goodbye|see you|talk soon|thanks|thank you)',
            r'^(great|perfect|excellent|sounds good)[\s!.]*$',
        ]
        
        for pattern in greetings:
            if re.match(pattern, text_lower):
                return True
        
        return len(text_lower.split()) <= 3 and not any(
            word in text_lower for word in ['will', 'should', 'need', 'must', 'task']
        )
    
    def _deduplicate_tasks(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate or very similar tasks."""
        if not tasks:
            return tasks
        
        unique_tasks = []
        seen_descriptions = set()
        
        for task in tasks:
            desc = task['description'].lower().strip()
            
            # Create a normalized version for comparison
            normalized = re.sub(r'\s+', ' ', desc)
            normalized = re.sub(r'[^\w\s]', '', normalized)
            
            # Check for similarity with existing tasks
            is_duplicate = False
            for seen in seen_descriptions:
                # Simple similarity: check if one is substring of another
                if normalized in seen or seen in normalized:
                    is_duplicate = True
                    break
                
                # Or if they share >70% of words
                desc_words = set(normalized.split())
                seen_words = set(seen.split())
                if desc_words and seen_words:
                    overlap = len(desc_words & seen_words) / max(len(desc_words), len(seen_words))
                    if overlap > 0.7:
                        is_duplicate = True
                        break
            
            if not is_duplicate:
                unique_tasks.append(task)
                seen_descriptions.add(normalized)
        
        return unique_tasks
    
    def _enhance_tasks(
        self, tasks: List[Dict[str, Any]], transcript_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Enhance tasks with additional metadata."""
        metadata = transcript_data.get('metadata', {})
        
        for task in tasks:
            # Add meeting metadata
            task['meeting_metadata'] = {
                'file': metadata.get('file', 'unknown'),
                'duration': metadata.get('duration', 0),
                'language': metadata.get('language', 'en')
            }
            
            # Format dates nicely
            if task.get('start_date'):
                task['start_date_formatted'] = task['start_date'].strftime('%B %d, %Y')
            if task.get('due_date'):
                task['due_date_formatted'] = task['due_date'].strftime('%B %d, %Y')
            
            # Add status field
            task['status'] = 'pending'
        
        # Sort by priority and due date
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        tasks.sort(key=lambda x: (
            priority_order.get(x['priority'], 3),
            x['due_date'] or datetime(2099, 12, 31)
        ))
        
        return tasks
