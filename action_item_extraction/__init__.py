"""
Action Item Extraction Module

This module extracts tasks, assignments, deadlines, and responsible persons
from meeting transcripts using advanced NLP techniques.
"""

from action_item_extraction.core.task_extractor import TaskExtractor
from action_item_extraction.extractor import extract_action_items

__all__ = ['TaskExtractor', 'extract_action_items']
