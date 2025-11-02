"""
Enhanced task patterns and urgency detection for task extraction.
"""

from typing import List, Tuple
import re


class TaskPatternLibrary:
    """Comprehensive library of task patterns for meeting transcripts."""
    
    @staticmethod
    def get_task_patterns() -> List[Tuple[str, str, str]]:
        """
        Get comprehensive task patterns.
        
        Returns:
            List of tuples (regex_pattern, priority, task_type)
        """
        return [
            # ========== HIGH PRIORITY PATTERNS ==========
            
            # Explicit requirements
            (r'\b(?:need to|needs to|needed to)\s+(.{5,150})', 'high', 'explicit'),
            (r'\b(?:have to|has to|had to|must|required to)\s+(.{5,150})', 'high', 'explicit'),
            (r'\b(?:critical|crucial|essential|vital)\s+(?:to|that we)\s+(.{5,150})', 'high', 'explicit'),
            
            # Urgent requests
            (r'\b(?:urgent|urgently|asap|as soon as possible)\b.*?(.{5,150})', 'high', 'urgent'),
            (r'\b(?:immediately|right away|right now)\s+(.{5,150})', 'high', 'urgent'),
            
            # Direct assignments
            (r'\b(?:responsible for|in charge of|assigned to|tasked with)\s+(.{5,150})', 'high', 'assignment'),
            (r'\b(?:your responsibility|you\'re responsible)\s+(?:to|for)\s+(.{5,150})', 'high', 'assignment'),
            
            # Action requests
            (r'\b(?:please|can you|could you|would you|will you)\s+(.{5,150})', 'high', 'request'),
            (r'\b(?:make sure|ensure|guarantee)\s+(?:to|that|we)\s+(.{5,150})', 'high', 'request'),
            
            # ========== MEDIUM PRIORITY PATTERNS ==========
            
            # Commitments and intentions
            (r'\b(?:will|\'ll|shall)\s+(.{5,150})', 'medium', 'commitment'),
            (r'\b(?:going to|gonna)\s+(.{5,150})', 'medium', 'commitment'),
            (r'\b(?:should|ought to|supposed to)\s+(.{5,150})', 'medium', 'explicit'),
            (r'\b(?:plan to|planning to|intend to)\s+(.{5,150})', 'medium', 'commitment'),
            
            # Collaborative actions
            (r'\b(?:let\'s|let us)\s+(.{5,150})', 'medium', 'collaborative'),
            (r'\b(?:we need to|we should|we have to)\s+(.{5,150})', 'medium', 'collaborative'),
            (r'\b(?:team needs to|group should)\s+(.{5,150})', 'medium', 'collaborative'),
            
            # Follow-up actions
            (r'\b(?:follow up|follow-up|followup)\s+(?:on|with)\s+(.{5,150})', 'medium', 'follow_up'),
            (r'\b(?:get back to|circle back|touch base)\s+(?:with|on)\s+(.{5,150})', 'medium', 'follow_up'),
            (r'\b(?:check in|sync up|catch up)\s+(?:with|on)\s+(.{5,150})', 'medium', 'follow_up'),
            
            # Specific action verbs - Documentation
            (r'\b(?:document|write down|note|record)\s+(.{5,150})', 'medium', 'documentation'),
            (r'\b(?:update|revise|modify|edit)\s+(?:the\s+)?(.{5,150})', 'medium', 'update'),
            
            # Specific action verbs - Creation
            (r'\b(?:create|build|develop|design|implement|set up)\s+(.{5,150})', 'medium', 'creation'),
            (r'\b(?:draft|prepare|put together|compile)\s+(.{5,150})', 'medium', 'creation'),
            
            # Specific action verbs - Communication
            (r'\b(?:send|email|share|distribute|forward)\s+(.{5,150})', 'medium', 'communication'),
            (r'\b(?:reach out|contact|get in touch|connect)\s+(?:to|with)\s+(.{5,150})', 'medium', 'communication'),
            (r'\b(?:schedule|arrange|organize|coordinate|set up)\s+(.{5,150})', 'medium', 'scheduling'),
            
            # Specific action verbs - Review/Analysis
            (r'\b(?:review|check|verify|validate|confirm)\s+(.{5,150})', 'medium', 'review'),
            (r'\b(?:analyze|evaluate|assess|examine|investigate)\s+(.{5,150})', 'medium', 'analysis'),
            (r'\b(?:test|quality check|qa)\s+(.{5,150})', 'medium', 'testing'),
            
            # Specific action verbs - Delivery
            (r'\b(?:deliver|submit|provide|present|show)\s+(.{5,150})', 'medium', 'delivery'),
            (r'\b(?:finish|complete|finalize|wrap up)\s+(.{5,150})', 'medium', 'completion'),
            
            # Ownership and leadership
            (r'\b(?:own|take ownership|drive|lead|spearhead)\s+(.{5,150})', 'medium', 'ownership'),
            (r'\b(?:manage|oversee|supervise|coordinate)\s+(.{5,150})', 'medium', 'management'),
            
            # ========== LOW PRIORITY PATTERNS ==========
            
            # Suggestions and possibilities
            (r'\b(?:could|might|may|perhaps)\s+(.{5,150})', 'low', 'suggestion'),
            (r'\b(?:consider|think about|look into)\s+(.{5,150})', 'low', 'suggestion'),
            (r'\b(?:would be good to|would be nice to|it\'d be great to)\s+(.{5,150})', 'low', 'suggestion'),
            
            # Assistance offers
            (r'\b(?:can help|happy to help|glad to)\s+(.{5,150})', 'low', 'offer'),
            (r'\b(?:if needed|if necessary|if required)\b.*?(.{5,150})', 'low', 'conditional'),
            
            # Self-commitments (I'll, I will, I can, I should)
            (r'\b(?:I\'ll|I will|I\'m going to|I can|I should)\s+(.{5,150})', 'medium', 'self_commitment'),
        ]
    
    @staticmethod
    def get_urgency_indicators() -> List[Tuple[str, float]]:
        """
        Get urgency indicators and their weight multipliers.
        
        Returns:
            List of tuples (pattern, priority_boost)
        """
        return [
            (r'\bASAP\b', 1.5),
            (r'\bas soon as possible\b', 1.5),
            (r'\burgent(?:ly)?\b', 1.4),
            (r'\bimmediate(?:ly)?\b', 1.4),
            (r'\bright (?:now|away)\b', 1.3),
            (r'\btop priority\b', 1.3),
            (r'\btime[- ]sensitive\b', 1.2),
            (r'\btime[- ]critical\b', 1.2),
            (r'\bby (?:today|tonight|tomorrow)\b', 1.2),
            (r'\bby end of (?:day|week)\b', 1.1),
            (r'\bimportant\b', 1.1),
            (r'\bcritical\b', 1.2),
        ]
    
    @staticmethod
    def get_importance_keywords() -> List[str]:
        """Get keywords that indicate task importance."""
        return [
            'important', 'critical', 'crucial', 'essential', 'vital',
            'key', 'main', 'primary', 'major', 'significant',
            'priority', 'urgent', 'pressing', 'immediate'
        ]
    
    @staticmethod
    def get_exclusion_patterns() -> List[str]:
        """Get patterns that should exclude a sentence from being a task."""
        return [
            r'^(?:hi|hey|hello|good morning|good afternoon)\b',  # Greetings
            r'^(?:bye|goodbye|see you|talk (?:soon|later))\b',  # Farewells
            r'^(?:thanks|thank you|appreciated)\b',  # Thanks
            r'^(?:great|perfect|excellent|awesome|sounds good)[\s!.]*$',  # Affirmations
            r'^(?:yes|yeah|yep|no|nope|okay|ok|sure|right)[\s!.]*$',  # Short responses
            r'\?$',  # Questions (usually not tasks unless rhetorical)
        ]
    
    @staticmethod
    def detect_urgency_level(text: str) -> Tuple[str, float]:
        """
        Detect urgency level from text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Tuple of (urgency_level, boost_factor)
        """
        text_lower = text.lower()
        max_boost = 1.0
        urgency_level = 'normal'
        
        for pattern, boost in TaskPatternLibrary.get_urgency_indicators():
            if re.search(pattern, text_lower):
                if boost > max_boost:
                    max_boost = boost
                    if boost >= 1.4:
                        urgency_level = 'critical'
                    elif boost >= 1.2:
                        urgency_level = 'high'
                    elif boost >= 1.1:
                        urgency_level = 'elevated'
        
        return urgency_level, max_boost
