"""
Semantic similarity utilities for task deduplication.
"""

import logging
from typing import List, Dict, Any, Tuple
import numpy as np

logger = logging.getLogger(__name__)

# Try to import sentence-transformers
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logger.warning("sentence-transformers not installed. Semantic deduplication will use basic methods.")


class SemanticDeduplicator:
    """Deduplicate tasks using semantic similarity."""
    
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2', similarity_threshold: float = 0.8):
        """
        Initialize the semantic deduplicator.
        
        Args:
            model_name: Name of the sentence transformer model
            similarity_threshold: Cosine similarity threshold for duplicates (0-1)
        """
        self.similarity_threshold = similarity_threshold
        self.model = None
        
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                logger.info(f"Loading sentence transformer model: {model_name}")
                self.model = SentenceTransformer(model_name)
                logger.info("Semantic deduplication enabled")
            except Exception as e:
                logger.warning(f"Failed to load sentence transformer: {e}")
                self.model = None
        else:
            logger.info("Using fallback deduplication (word-based)")
    
    def deduplicate_tasks(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Remove duplicate tasks using semantic similarity.
        
        Args:
            tasks: List of task dictionaries
            
        Returns:
            List of unique tasks
        """
        if not tasks:
            return tasks
        
        if self.model is not None:
            return self._semantic_deduplicate(tasks)
        else:
            return self._fallback_deduplicate(tasks)
    
    def _semantic_deduplicate(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Deduplicate using sentence embeddings."""
        # Extract descriptions
        descriptions = [task['description'] for task in tasks]
        
        # Encode descriptions
        embeddings = self.model.encode(descriptions, convert_to_numpy=True)
        
        # Calculate pairwise cosine similarities
        similarities = self._cosine_similarity_matrix(embeddings)
        
        # Find duplicates
        unique_indices = []
        duplicate_groups = []
        seen = set()
        
        for i in range(len(tasks)):
            if i in seen:
                continue
            
            # Find all tasks similar to this one
            similar_indices = [i]
            for j in range(i + 1, len(tasks)):
                if j in seen:
                    continue
                
                if similarities[i, j] >= self.similarity_threshold:
                    similar_indices.append(j)
                    seen.add(j)
            
            # Keep the best task from this group
            best_task_idx = self._select_best_task(tasks, similar_indices)
            unique_indices.append(best_task_idx)
            
            if len(similar_indices) > 1:
                duplicate_groups.append(similar_indices)
        
        unique_tasks = [tasks[i] for i in unique_indices]
        
        logger.info(f"Semantic deduplication: {len(tasks)} -> {len(unique_tasks)} tasks")
        if duplicate_groups:
            logger.debug(f"Found {len(duplicate_groups)} groups of duplicates")
        
        return unique_tasks
    
    def _fallback_deduplicate(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Fallback deduplication using word overlap."""
        import re
        
        unique_tasks = []
        seen_descriptions = []
        
        for task in tasks:
            description = task['description'].lower().strip()
            
            # Normalize
            normalized = re.sub(r'\s+', ' ', description)
            normalized = re.sub(r'[^\w\s]', '', normalized)
            words = set(normalized.split())
            
            # Check similarity with existing tasks
            is_duplicate = False
            
            for seen_desc in seen_descriptions:
                seen_words = set(seen_desc.split())
                
                if not words or not seen_words:
                    continue
                
                # Jaccard similarity
                intersection = len(words & seen_words)
                union = len(words | seen_words)
                similarity = intersection / union if union > 0 else 0
                
                # Also check substring containment
                substring_match = (normalized in ' '.join(seen_descriptions) or 
                                 ' '.join(seen_descriptions) in normalized)
                
                if similarity >= 0.7 or substring_match:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_tasks.append(task)
                seen_descriptions.append(normalized)
        
        logger.info(f"Fallback deduplication: {len(tasks)} -> {len(unique_tasks)} tasks")
        return unique_tasks
    
    def _cosine_similarity_matrix(self, embeddings: np.ndarray) -> np.ndarray:
        """Calculate cosine similarity matrix for embeddings."""
        # Normalize embeddings
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        normalized = embeddings / (norms + 1e-8)
        
        # Compute similarity matrix
        similarity_matrix = np.dot(normalized, normalized.T)
        
        return similarity_matrix
    
    def _select_best_task(
        self,
        tasks: List[Dict[str, Any]],
        indices: List[int]
    ) -> int:
        """
        Select the best task from a group of similar tasks.
        
        Priority:
        1. Task with assignee
        2. Task with due date
        3. Highest confidence
        4. Longest description
        """
        candidates = [(i, tasks[i]) for i in indices]
        
        # Score each candidate
        def score_task(task: Dict[str, Any]) -> Tuple[int, int, float, int]:
            has_assignee = 1 if (task.get('assignee') and task['assignee'] != 'Unassigned') else 0
            has_due_date = 1 if task.get('due_date') else 0
            confidence = task.get('confidence', 0.0)
            desc_length = len(task['description'])
            
            return (has_assignee, has_due_date, confidence, desc_length)
        
        # Sort by score (descending)
        candidates.sort(key=lambda x: score_task(x[1]), reverse=True)
        
        return candidates[0][0]
    
    def get_similarity_score(self, text1: str, text2: str) -> float:
        """
        Get semantic similarity score between two texts.
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Similarity score (0-1)
        """
        if self.model is not None:
            embeddings = self.model.encode([text1, text2], convert_to_numpy=True)
            similarity = np.dot(embeddings[0], embeddings[1]) / (
                np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[1])
            )
            return float(similarity)
        else:
            # Fallback: Jaccard similarity
            import re
            words1 = set(re.findall(r'\w+', text1.lower()))
            words2 = set(re.findall(r'\w+', text2.lower()))
            
            if not words1 or not words2:
                return 0.0
            
            intersection = len(words1 & words2)
            union = len(words1 | words2)
            
            return intersection / union if union > 0 else 0.0
