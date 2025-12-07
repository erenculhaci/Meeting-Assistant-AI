"""
LLM-based Action Item Extractor using Few-Shot Learning.

Uses Groq API with few-shot examples for accurate action item extraction.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Check if Groq is available
try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    logger.warning("groq not installed. LLM extraction will be disabled.")


class LLMActionItemExtractor:
    """Extract action items using LLM with few-shot learning."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "llama-3.3-70b-versatile"  # Updated to latest model
    ):
        """
        Initialize LLM extractor.
        
        Args:
            api_key: Groq API key (uses env var if not provided)
            model: Model to use
        """
        self.model = model
        self.client = None
        self.enabled = False
        
        if not GROQ_AVAILABLE:
            logger.warning("Groq not available. LLM extraction disabled.")
            return
        
        # Initialize Groq client
        key = api_key or os.getenv("GROQ_API_KEY")
        if not key:
            logger.warning("No Groq API key found. LLM extraction disabled.")
            return
        
        try:
            self.client = Groq(api_key=key)
            self.enabled = True
            logger.info(f"LLM extractor initialized with {self.model}")
        except Exception as e:
            logger.error(f"Failed to initialize Groq client: {e}")
            self.enabled = False
    
    def extract_action_items(
        self,
        transcript_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Extract action items from transcript using LLM.
        
        Args:
            transcript_data: Transcript with segments
            
        Returns:
            Extraction results with action items
        """
        if not self.enabled:
            return {
                'status': 'error',
                'message': 'LLM extraction not available',
                'action_items': []
            }
        
        segments = transcript_data.get('transcript', [])
        
        # Build conversation context with segment tracking
        conversation, segment_map = self._build_conversation_text_with_map(segments)
        
        # Extract speakers
        speakers = list(set(seg.get('speaker', '').replace('Speaker_', '') 
                           for seg in segments if seg.get('speaker')))
        
        # Call LLM with few-shot examples
        try:
            action_items = self._extract_with_llm(conversation, speakers, segments, segment_map)
            
            return {
                'status': 'success',
                'action_items': action_items,
                'total_items': len(action_items),
                'extraction_method': 'llm_few_shot',
                'model': self.model
            }
        except Exception as e:
            logger.error(f"LLM extraction failed: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'action_items': []
            }
    
    def _build_conversation_text(self, segments: List[Dict]) -> str:
        """Build formatted conversation text from segments."""
        lines = []
        for seg in segments:
            speaker = seg.get('speaker', 'Unknown').replace('Speaker_', '')
            text = seg.get('text', '').strip()
            if text:
                lines.append(f"{speaker}: {text}")
        return '\n'.join(lines)
    
    def _build_conversation_text_with_map(self, segments: List[Dict]) -> tuple:
        """
        Build formatted conversation text with segment mapping.
        Returns (conversation_text, segment_map) where segment_map maps line numbers to segment indices.
        """
        lines = []
        segment_map = {}  # line_number -> segment_index
        
        for idx, seg in enumerate(segments):
            speaker = seg.get('speaker', 'Unknown').replace('Speaker_', '')
            text = seg.get('text', '').strip()
            if text:
                segment_map[len(lines)] = idx
                lines.append(f"{speaker}: {text}")
        
        return '\n'.join(lines), segment_map
    
    def _extract_with_llm(
        self,
        conversation: str,
        speakers: List[str],
        segments: List[Dict],
        segment_map: Dict[int, int]
    ) -> List[Dict[str, Any]]:
        """Extract action items using LLM with few-shot prompting."""
        
        prompt = self._build_few_shot_prompt(conversation, speakers)
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert at extracting action items from meeting transcripts. You identify tasks, assignees, deadlines, and start dates accurately."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.1,  # Low temperature for consistent extraction
            max_tokens=2000
        )
        
        # Parse response
        try:
            result_text = response.choices[0].message.content.strip()
            
            # Extract JSON from response (might be wrapped in ```json```)
            if '```json' in result_text:
                json_start = result_text.find('```json') + 7
                json_end = result_text.find('```', json_start)
                result_text = result_text[json_start:json_end].strip()
            elif '```' in result_text:
                json_start = result_text.find('```') + 3
                json_end = result_text.find('```', json_start)
                result_text = result_text[json_start:json_end].strip()
            
            result = json.loads(result_text)
            action_items = result.get('action_items', [])
            
            # Post-process: clean, validate, and find speakers from transcript
            cleaned_items = []
            for item in action_items:
                cleaned = self._clean_action_item(item, segments, conversation)
                if cleaned:
                    cleaned_items.append(cleaned)
            
            return cleaned_items
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response: {e}")
            logger.debug(f"Response text: {result_text}")
            return []
    
    def _build_few_shot_prompt(
        self,
        conversation: str,
        speakers: List[str]
    ) -> str:
        """Build few-shot prompt with examples."""
        
        speaker_list = ", ".join(speakers) if speakers else "unknown"
        
        return f"""Extract action items from the following meeting transcript.

PARTICIPANTS: {speaker_list}

TRANSCRIPT:
{conversation}

Extract all action items and return them as JSON in this exact format:
{{
  "action_items": [
    {{
      "description": "clear, actionable task description",
      "assignee": "Name" or "Name1 and Name2" or "Unassigned",
      "due_date": "specific deadline" or null,
      "start_date": "when task should start" or null,
      "confidence": 0.0-1.0
    }}
  ]
}}

CRITICAL RULES:
1. ASSIGNEE FORMAT:
   - Use ONLY plain names (e.g., "Sarah", "Brian") - NEVER "Speaker_" prefix
   - For multiple assignees: "Name1 and Name2" (e.g., "Paul and Laura")
   - If unclear or general: "Unassigned"
   - Names must be from participants list: {speaker_list}

2. DESCRIPTION:
   - Must be clear and actionable (verb + object)
   - Examples: "prepare quarterly report", "review security vulnerabilities"
   - NOT fragments like "for the visuals" or "that thing"

3. DUE_DATE:
   - Extract exact deadline mentioned (e.g., "next Monday", "by end of month", "November 20th")
   - If no deadline mentioned: null
   - Keep original format from conversation

4. START_DATE:
   - Extract when task should start (e.g., "starting November 2nd", "begin on Monday")
   - If no start date mentioned: null
   - Keep original format from conversation

5. CONFIDENCE:
   - 0.9-1.0: Explicit assignment with clear task
   - 0.7-0.9: Clear task, implicit assignment
   - 0.5-0.7: Ambiguous or general statement
   - Only include items with confidence >= 0.5

FEW-SHOT EXAMPLES:

Example 1:
TRANSCRIPT:
Manager: We need someone to prepare the quarterly report.
Laura: I'll handle that by next Monday.
Manager: Great, thanks.

OUTPUT:
{{
  "action_items": [
    {{
      "description": "prepare the quarterly report",
      "assignee": "Laura",
      "due_date": "next Monday",
      "start_date": null,
      "confidence": 0.95
    }}
  ]
}}

Example 2:
TRANSCRIPT:
Manager: Brian, could you create the architecture diagram?
Brian: Sure, I'll get that done.
Manager: Also, Paul and Laura, could you both work together on the security audit by month end?
Paul: Sounds good.
Laura: Yes, we'll handle it.

OUTPUT:
{{
  "action_items": [
    {{
      "description": "create the architecture diagram",
      "assignee": "Brian",
      "due_date": null,
      "start_date": null,
      "confidence": 0.95
    }},
    {{
      "description": "work on the security audit",
      "assignee": "Laura and Paul",
      "due_date": "by month end",
      "start_date": null,
      "confidence": 0.95
    }}
  ]
}}

Example 3:
TRANSCRIPT:
Manager: Maya, you should start the backend analysis on November 2nd and deliver the report by November 18th.
Maya: Understood, I'll begin on the 2nd.

OUTPUT:
{{
  "action_items": [
    {{
      "description": "start backend analysis and deliver report",
      "assignee": "Maya",
      "due_date": "November 18th",
      "start_date": "November 2nd",
      "confidence": 0.95
    }}
  ]
}}

Example 3:
TRANSCRIPT:
Manager: Someone needs to update the documentation.
Team: We should do that soon.
Manager: Let's make sure it gets done.

OUTPUT:
{{
  "action_items": [
    {{
      "description": "update the documentation",
      "assignee": "Unassigned",
      "due_date": null,
      "confidence": 0.7
    }}
  ]
}}

Now extract action items from the given transcript above. Return ONLY the JSON, no additional text."""
    
    def _clean_action_item(self, item: Dict, segments: List[Dict], conversation: str) -> Optional[Dict]:
        """Clean and validate an action item, find speaker from transcript."""
        description = item.get('description', '').strip()
        assignee = item.get('assignee', 'Unassigned').strip()
        due_date = item.get('due_date')
        start_date = item.get('start_date')
        confidence = item.get('confidence', 0.7)
        
        # Validate description
        if not description or len(description.split()) < 2:
            return None
        
        # Clean assignee (remove Speaker_ if present)
        assignee = assignee.replace('Speaker_', '')
        
        # Validate confidence
        if confidence < 0.5:
            return None
        
        # Find speaker from transcript by matching description or assignee
        speaker = self._find_speaker_from_transcript(description, assignee, segments, conversation)
        
        return {
            'description': description,
            'assignee': assignee,
            'speaker': speaker,
            'due_date': due_date,
            'start_date': start_date,
            'confidence': confidence,
            'source': description,  # Use description as source
            'extraction_method': 'llm',
            'priority': 'medium'
        }
    
    def _find_speaker_from_transcript(
        self,
        description: str,
        assignee: str,
        segments: List[Dict],
        conversation: str
    ) -> str:
        """
        Find the speaker who mentioned this action item.
        
        Strategy:
        1. Look for segment where assignee is mentioned
        2. Look for segment containing key words from description
        3. Return the speaker of that segment
        """
        desc_lower = description.lower()
        assignee_lower = assignee.lower()
        
        # Get key words from description (verbs and nouns)
        key_words = [w for w in desc_lower.split() if len(w) > 3][:3]
        
        # Search segments for best match
        best_speaker = 'Unknown'
        best_score = 0
        
        for seg in segments:
            text = seg.get('text', '').lower()
            speaker = seg.get('speaker', 'Unknown').replace('Speaker_', '')
            
            score = 0
            
            # Check if assignee is mentioned (strong signal)
            if assignee_lower in text and assignee_lower != 'unassigned':
                score += 10
            
            # Check if key words from description are in text
            for word in key_words:
                if word in text:
                    score += 2
            
            # Prefer segments from people assigning tasks (not the assignee themselves)
            if speaker.lower() != assignee_lower:
                score += 1
            
            if score > best_score:
                best_score = score
                best_speaker = speaker
        
        return best_speaker if best_speaker != 'Unknown' else segments[0].get('speaker', 'Unknown').replace('Speaker_', '') if segments else 'Unknown'


def main():
    """Test LLM extractor."""
    test_transcript = {
        'transcript': [
            {'text': "We need someone to prepare the quarterly report.", 'speaker': 'Speaker_Manager'},
            {'text': "I'll handle that by next Monday.", 'speaker': 'Speaker_Laura'},
            {'text': "Great, thanks.", 'speaker': 'Speaker_Manager'},
            {'text': "Brian, could you create the architecture diagram?", 'speaker': 'Speaker_Manager'},
            {'text': "Sure, will do.", 'speaker': 'Speaker_Brian'},
            {'text': "Paul and Laura, could you both work together on the security audit?", 'speaker': 'Speaker_Manager'},
            {'text': "Sounds good.", 'speaker': 'Speaker_Paul'},
            {'text': "Yes, we'll handle it by month end.", 'speaker': 'Speaker_Laura'},
        ]
    }
    
    extractor = LLMActionItemExtractor()
    
    if not extractor.enabled:
        print("❌ LLM extraction not available. Check Groq API key.")
        return
    
    print("🔍 Testing LLM Action Item Extraction\n")
    results = extractor.extract_action_items(test_transcript)
    
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
