"""
Summarization Module
====================
Provides meeting summarization capabilities using both local BART and cloud LLM.

Usage:
    # LLM-based
    from summarization.llm_summarizer import LLMSummarizer, summarize_meeting_llm
    
    # Local BART-based (offline capable)
    from summarization.summarizer import summarize_meeting
"""

from summarization.llm_summarizer import LLMSummarizer, summarize_meeting_llm

__all__ = ['LLMSummarizer', 'summarize_meeting_llm']
