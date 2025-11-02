"""
Utilities for the action item extraction module.
"""

from action_item_extraction.utils.date_parser import DateParser
from action_item_extraction.utils.person_extractor import PersonExtractor
from action_item_extraction.utils.task_patterns import TaskPatternLibrary
from action_item_extraction.utils.confidence_model import TaskConfidenceModel
from action_item_extraction.utils.semantic_dedup import SemanticDeduplicator

__all__ = [
    'DateParser',
    'PersonExtractor',
    'TaskPatternLibrary',
    'TaskConfidenceModel',
    'SemanticDeduplicator'
]
