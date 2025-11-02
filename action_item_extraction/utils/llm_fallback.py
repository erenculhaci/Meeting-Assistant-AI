"""
LLM Fallback for ambiguous task extraction.
Uses OpenAI API to clarify unclear tasks, assignees, and descriptions.
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)

# Check if OpenAI is available
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("openai not installed. LLM fallback will be disabled.")

# Check if Groq is available
try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False


class LLMTaskClarifier:
    """
    Uses LLM to clarify ambiguous or low-confidence tasks.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o-mini",
        enabled: bool = True,
        confidence_threshold: float = 0.7,
        provider: str = "auto"  # "auto", "openai", "groq"
    ):
        """
        Initialize LLM clarifier.
        
        Args:
            api_key: API key (uses env var if not provided)
            model: Model to use
            enabled: Whether to use LLM fallback
            confidence_threshold: Use LLM for tasks below this confidence
            provider: LLM provider ("auto", "openai", "groq")
        """
        self.enabled = enabled
        self.model = model
        self.confidence_threshold = confidence_threshold
        self.provider = provider
        self.client = None
        
        if not self.enabled:
            logger.info("LLM clarifier disabled")
            return
        
        # Auto-detect provider
        if provider == "auto":
            if os.getenv("GROQ_API_KEY") and GROQ_AVAILABLE:
                self.provider = "groq"
            elif os.getenv("OPENAI_API_KEY") and OPENAI_AVAILABLE:
                self.provider = "openai"
            else:
                logger.warning("No API key found. LLM fallback disabled.")
                self.enabled = False
                return
        
        # Initialize provider
        if self.provider == "groq" and GROQ_AVAILABLE:
            self._init_groq(api_key)
        elif self.provider == "openai" and OPENAI_AVAILABLE:
            self._init_openai(api_key)
        else:
            logger.warning(f"Provider {self.provider} not available. LLM fallback disabled.")
            self.enabled = False
        
        if self.enabled:
            logger.info(f"LLM clarifier enabled with {self.provider} ({self.model})")
    
    def _init_groq(self, api_key: Optional[str] = None):
        """Initialize Groq client."""
        try:
            from groq import Groq
            
            key = api_key or os.getenv("GROQ_API_KEY")
            if not key:
                logger.warning("No Groq API key found.")
                self.enabled = False
                return
            
            # Initialize Groq client (simpler initialization)
            self.client = Groq(api_key=key)
            
            # Map to Groq models
            model_map = {
                "gpt-4o-mini": "llama-3.1-8b-instant",
                "gpt-4o": "llama-3.1-70b-versatile",
                "gpt-4": "llama-3.1-70b-versatile",
            }
            self.model = model_map.get(self.model, "llama-3.1-8b-instant")
            
        except Exception as e:
            logger.error(f"Failed to initialize Groq: {e}")
            self.enabled = False
    
    def _init_openai(self, api_key: Optional[str] = None):
        """Initialize OpenAI client."""
        try:
            key = api_key or os.getenv("OPENAI_API_KEY")
            if not key:
                logger.warning("No OpenAI API key found.")
                self.enabled = False
                return
            
            openai.api_key = key
            
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI: {e}")
            self.enabled = False
    
    def should_clarify(self, task: Dict[str, Any]) -> bool:
        """
        Determine if a task needs LLM clarification.
        
        Args:
            task: Task dictionary
            
        Returns:
            True if task should be clarified
        """
        if not self.enabled:
            return False
        
        # Low confidence tasks
        if task.get('confidence', 1.0) < self.confidence_threshold:
            return True
        
        # Invalid assignees (common false positives)
        invalid_assignees = [
            'that', 'this', 'it', 'yes', 'no', 'okay', 'alright',
            'yeah', 'yep', 'sure', 'right', 'good', 'great', 'perfect'
        ]
        assignee = task.get('assignee', '').lower()
        if assignee in invalid_assignees:
            return True
        
        # Very short or unclear descriptions
        description = task.get('description', '')
        if len(description) < 20:
            return True
        
        # Description is just a fragment
        if description.startswith(('for the', 'with', 'and', 'or', 'but')):
            return True
        
        return False
    
    def clarify_task(
        self,
        task: Dict[str, Any],
        context: List[Dict[str, str]],
        speakers: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Use LLM to clarify an ambiguous task.
        
        Args:
            task: Task to clarify
            context: Surrounding segments for context
            speakers: List of known speakers
            
        Returns:
            Clarified task or original if clarification fails
        """
        if not self.enabled:
            return task
        
        try:
            # Build context
            context_text = "\n".join([
                f"{seg.get('speaker', 'Unknown')}: {seg.get('text', '')}"
                for seg in context[-5:]  # Last 5 segments
            ])
            
            # Build prompt
            prompt = self._build_clarification_prompt(
                task=task,
                context=context_text,
                speakers=speakers or []
            )
            
            # Call LLM (provider-specific)
            if self.provider == "groq":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a meeting assistant that extracts clear, actionable tasks from meeting transcripts."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.3,
                    max_tokens=300,
                    response_format={"type": "json_object"}
                )
            else:  # openai
                response = openai.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a meeting assistant that extracts clear, actionable tasks from meeting transcripts."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.3,
                    max_tokens=300,
                    response_format={"type": "json_object"}
                )
            
            # Parse response
            clarified = json.loads(response.choices[0].message.content)
            
            # Validate and merge
            return self._merge_clarification(task, clarified)
            
        except Exception as e:
            logger.error(f"LLM clarification failed: {str(e)}")
            return task
    
    def _build_clarification_prompt(
        self,
        task: Dict[str, Any],
        context: str,
        speakers: List[str]
    ) -> str:
        """Build prompt for LLM clarification."""
        
        speaker_list = ", ".join(speakers) if speakers else "unknown"
        
        return f"""Given this meeting context, clarify the following task:

CONTEXT:
{context}

EXTRACTED TASK:
- Description: {task.get('description', '')}
- Assignee: {task.get('assignee', 'Unassigned')}
- Source: {task.get('source', '')}

KNOWN SPEAKERS: {speaker_list}

Please analyze this and return a JSON with:
{{
    "is_valid_task": true/false,  // Is this actually a task?
    "description": "Clear, actionable task description",
    "assignee": "Name or 'Unassigned'",  // Must be a real person from speakers list
    "reasoning": "Brief explanation of your analysis",
    "confidence": 0.0-1.0  // Your confidence in this clarification
}}

RULES:
1. If assignee is not a real person name or speaker ID, use "Unassigned"
2. Description should be clear and actionable (not fragments like "for the visuals")
3. If this isn't really a task (e.g., just a statement), set is_valid_task to false
4. Be concise but clear
"""
    
    def _merge_clarification(
        self,
        original: Dict[str, Any],
        clarified: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Merge LLM clarification with original task.
        
        Args:
            original: Original task
            clarified: LLM clarification
            
        Returns:
            Merged task
        """
        # If LLM says not a valid task, mark for removal
        if not clarified.get('is_valid_task', True):
            original['llm_marked_invalid'] = True
            original['llm_reasoning'] = clarified.get('reasoning', '')
            return original
        
        # Update with clarified values
        merged = original.copy()
        
        if clarified.get('description'):
            merged['description'] = clarified['description']
        
        if clarified.get('assignee') and clarified['assignee'] != 'Unassigned':
            merged['assignee'] = clarified['assignee']
        
        # Update confidence if LLM is confident
        llm_confidence = clarified.get('confidence', 0.0)
        if llm_confidence > 0.7:
            merged['confidence'] = max(original.get('confidence', 0.5), llm_confidence)
        
        # Add metadata
        merged['llm_clarified'] = True
        merged['llm_reasoning'] = clarified.get('reasoning', '')
        
        logger.info(f"LLM clarified task: {original.get('description')[:50]}... -> {merged.get('description')[:50]}...")
        
        return merged
    
    def batch_clarify(
        self,
        tasks: List[Dict[str, Any]],
        transcript_segments: List[Dict[str, str]],
        speakers: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Clarify multiple tasks in batch.
        
        Args:
            tasks: List of tasks to potentially clarify
            transcript_segments: Full transcript for context
            speakers: List of known speakers
            
        Returns:
            List of clarified tasks with invalid ones removed
        """
        if not self.enabled:
            return tasks
        
        clarified_tasks = []
        
        for i, task in enumerate(tasks):
            if self.should_clarify(task):
                logger.info(f"Clarifying task {i+1}/{len(tasks)}: {task.get('description', '')[:50]}...")
                
                # Find context around this task
                segment_idx = task.get('segment_index', 0)
                context_start = max(0, segment_idx - 2)
                context_end = min(len(transcript_segments), segment_idx + 3)
                context = transcript_segments[context_start:context_end]
                
                # Clarify
                clarified = self.clarify_task(task, context, speakers)
                
                # Only keep if valid
                if not clarified.get('llm_marked_invalid', False):
                    clarified_tasks.append(clarified)
                else:
                    logger.info(f"LLM marked task as invalid: {clarified.get('llm_reasoning', '')}")
            else:
                clarified_tasks.append(task)
        
        logger.info(f"LLM clarification: {len(tasks)} -> {len(clarified_tasks)} tasks")
        
        return clarified_tasks
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics (for cost tracking)."""
        # This would track API calls, tokens, etc.
        # For now, just return basic info
        return {
            'enabled': self.enabled,
            'model': self.model,
            'confidence_threshold': self.confidence_threshold
        }
