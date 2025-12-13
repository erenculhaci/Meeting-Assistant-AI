import re
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class TaskConfidenceModel:
    def __init__(self):
        """Initialize the confidence model."""
        self.feature_weights = {
            'has_assignee': 0.20,
            'has_due_date': 0.15,
            'has_start_date': 0.05,
            'task_length': 0.10,
            'has_action_verb': 0.15,
            'modal_verb_strength': 0.10,
            'context_quality': 0.10,
            'urgency_level': 0.10,
            'sentence_structure': 0.05,
        }
        
        # Modal verbs ranked by commitment strength
        self.modal_verbs = {
            'must': 1.0,
            'have to': 1.0,
            'has to': 1.0,
            'need to': 0.95,
            'needs to': 0.95,
            'will': 0.9,
            'shall': 0.85,
            'should': 0.7,
            'ought to': 0.7,
            'going to': 0.8,
            'gonna': 0.75,
            'could': 0.4,
            'might': 0.3,
            'may': 0.3,
            'can': 0.5,
        }
        
        # Strong action verbs
        self.action_verbs = {
            'complete', 'finish', 'deliver', 'submit', 'send', 'provide',
            'create', 'build', 'develop', 'implement', 'design',
            'review', 'check', 'verify', 'validate', 'confirm',
            'schedule', 'arrange', 'organize', 'coordinate',
            'update', 'revise', 'modify', 'prepare', 'draft',
            'analyze', 'evaluate', 'assess', 'test'
        }
    
    def calculate_confidence(
        self,
        task: Dict[str, Any],
        context_segments: list = None
    ) -> float:
        
        features = self._extract_features(task, context_segments)
        confidence = self._compute_weighted_score(features)
        
        return min(max(confidence, 0.0), 1.0)  # Clamp between 0 and 1
    
    def _extract_features(
        self,
        task: Dict[str, Any],
        context_segments: list = None
    ) -> Dict[str, float]:
        features = {}
        
        description = task.get('description', '').lower()
        source_text = task.get('source_text', '').lower()
        
        # Feature 1: Has assignee
        assignee = task.get('assignee', '')
        features['has_assignee'] = 1.0 if (assignee and assignee != 'Unassigned') else 0.0
        
        # Feature 2: Has due date
        features['has_due_date'] = 1.0 if task.get('due_date') else 0.0
        
        # Feature 3: Has start date
        features['has_start_date'] = 1.0 if task.get('start_date') else 0.0
        
        # Feature 4: Task length quality (prefer 15-60 words)
        word_count = len(description.split())
        if 15 <= word_count <= 60:
            features['task_length'] = 1.0
        elif 10 <= word_count < 15 or 60 < word_count <= 80:
            features['task_length'] = 0.7
        elif 5 <= word_count < 10:
            features['task_length'] = 0.5
        else:
            features['task_length'] = 0.3
        
        # Feature 5: Has strong action verb
        has_action_verb = any(verb in description for verb in self.action_verbs)
        features['has_action_verb'] = 1.0 if has_action_verb else 0.3
        
        # Feature 6: Modal verb strength
        modal_strength = 0.0
        for modal, strength in self.modal_verbs.items():
            if re.search(r'\b' + re.escape(modal) + r'\b', source_text):
                modal_strength = max(modal_strength, strength)
        features['modal_verb_strength'] = modal_strength
        
        # Feature 7: Context quality (from source text)
        context_score = self._evaluate_context_quality(source_text)
        features['context_quality'] = context_score
        
        # Feature 8: Urgency level
        urgency_score = self._evaluate_urgency(source_text)
        features['urgency_level'] = urgency_score
        
        # Feature 9: Sentence structure (imperative, declarative, etc.)
        structure_score = self._evaluate_sentence_structure(source_text)
        features['sentence_structure'] = structure_score
        
        return features
    
    def _compute_weighted_score(self, features: Dict[str, float]) -> float:
        total_score = 0.0
        
        for feature_name, weight in self.feature_weights.items():
            feature_value = features.get(feature_name, 0.0)
            total_score += feature_value * weight
        
        # Base confidence
        base_confidence = 0.3
        
        return base_confidence + (total_score * 0.7)
    
    def _evaluate_context_quality(self, text: str) -> float:
        score = 0.5  # Base score
        
        # Check for specific context indicators
        if re.search(r'\b(please|could you|can you|would you)\b', text):
            score += 0.2
        
        if re.search(r'\b(responsible|assigned|tasked)\b', text):
            score += 0.2
        
        if re.search(r'\b(deadline|due|by)\b', text):
            score += 0.1
        
        # Penalize vague language
        if re.search(r'\b(maybe|perhaps|possibly|might want to)\b', text):
            score -= 0.2
        
        # Penalize questions
        if text.strip().endswith('?'):
            score -= 0.1
        
        return min(max(score, 0.0), 1.0)
    
    def _evaluate_urgency(self, text: str) -> float:
        score = 0.5  # Base
        
        urgent_keywords = [
            (r'\b(asap|urgent|immediate|critical)\b', 0.5),
            (r'\b(today|tonight|right now|right away)\b', 0.3),
            (r'\b(important|priority|essential)\b', 0.2),
        ]
        
        for pattern, boost in urgent_keywords:
            if re.search(pattern, text, re.IGNORECASE):
                score = min(score + boost, 1.0)
        
        return score
    
    def _evaluate_sentence_structure(self, text: str) -> float:
        score = 0.5
        
        # Imperative sentences (commands) are strong task indicators
        if re.match(r'^(?:please\s+)?(?:can you\s+)?(?:could you\s+)?[a-z]+\b', text.lower()):
            score += 0.3
        
        # Declarative with clear subject and action
        if re.search(r'\b(will|should|need to|have to)\s+[a-z]+', text.lower()):
            score += 0.2
        
        # Complete sentence structure
        if '.' in text or len(text.split()) > 8:
            score += 0.1
        
        # Penalize fragments
        if len(text.split()) < 5:
            score -= 0.2
        
        return min(max(score, 0.0), 1.0)
    
    def get_confidence_explanation(
        self,
        task: Dict[str, Any],
        context_segments: list = None
    ) -> Dict[str, Any]:
        features = self._extract_features(task, context_segments)
        confidence = self._compute_weighted_score(features)
        
        return {
            'confidence': min(max(confidence, 0.0), 1.0),
            'features': features,
            'weights': self.feature_weights,
            'breakdown': {
                feature: features.get(feature, 0.0) * weight
                for feature, weight in self.feature_weights.items()
            }
        }
