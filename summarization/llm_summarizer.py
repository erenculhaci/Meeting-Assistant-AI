"""
LLM-based Meeting Summarizer
============================
Uses cloud LLM API for fast, high-quality meeting summarization.
Much faster than local BART and produces better structured output.
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from groq import Groq
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


@dataclass
class MeetingSummaryResult:
    """Structured meeting summary result"""
    title: str
    overview: str
    key_points: List[str]
    decisions: List[str]
    discussion_topics: List[Dict[str, str]]
    next_steps: List[str]
    participants: List[str]
    duration: float
    model: str
    processing_time: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class LLMSummarizer:
    """
    Meeting summarizer using cloud LLM API.
    
    Features:
    - Fast inference (~2-5 seconds)
    - Structured output with key points, decisions, topics
    - Participant extraction
    - Markdown and JSON export
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "llama-3.3-70b-versatile"
    ):
        """
        Initialize LLM Summarizer.
        
        Args:
            api_key: API key (or set GROQ_API_KEY env variable)
            model: LLM model to use
        """
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError(
                "API key required. Set GROQ_API_KEY environment variable."
            )
        
        self.client = Groq(api_key=self.api_key)
        self.model = model
        logger.info(f"LLMSummarizer initialized with model: {model}")
    
    def _build_transcript_text(self, transcript_data: Dict) -> str:
        """Convert transcript JSON to readable text format."""
        segments = transcript_data.get('transcript', [])
        
        lines = []
        for seg in segments:
            speaker = seg.get('speaker', 'Unknown')
            text = seg.get('text', '').strip()
            if text:
                lines.append(f"{speaker}: {text}")
        
        return "\n".join(lines)
    
    def _build_prompt(self, transcript_text: str) -> str:
        """Build the summarization prompt."""
        return f"""You are an expert meeting analyst. Analyze this meeting transcript and provide a comprehensive summary.

## Meeting Transcript:
{transcript_text}

## Instructions:
Analyze the transcript and extract the following information. Be specific and use actual names/details from the meeting.

Respond in this exact JSON format:
{{
    "title": "A concise title for this meeting (max 10 words)",
    "overview": "A 2-3 sentence executive summary of the entire meeting",
    "key_points": [
        "Key point 1 - be specific with names and details",
        "Key point 2",
        "Key point 3",
        "... (include all important points, typically 3-7)"
    ],
    "decisions": [
        "Decision 1 that was made during the meeting",
        "Decision 2",
        "... (list all decisions made, or empty array if none)"
    ],
    "discussion_topics": [
        {{"topic": "Topic name", "summary": "Brief summary of what was discussed about this topic"}},
        {{"topic": "Another topic", "summary": "Summary of this discussion"}}
    ],
    "next_steps": [
        "Next step or follow-up item 1",
        "Next step 2",
        "... (actionable next steps mentioned)"
    ],
    "participants": [
        "Name or identifier of participant 1",
        "Participant 2",
        "... (all identified speakers/participants)"
    ]
}}

Important:
- Extract ONLY information that is actually in the transcript
- Use specific names, dates, and details when mentioned
- If a section has no relevant content, use an empty array []
- Keep the overview concise but informative
- Respond with valid JSON only, no additional text"""

    def summarize(
        self,
        transcript_data: Dict,
        max_tokens: int = 2000,
        temperature: float = 0.3
    ) -> MeetingSummaryResult:
        """
        Summarize a meeting transcript.
        
        Args:
            transcript_data: Transcript data dictionary (from transcription)
            max_tokens: Maximum tokens in response
            temperature: LLM temperature (lower = more focused)
            
        Returns:
            MeetingSummaryResult with structured summary
        """
        start_time = datetime.now()
        
        # Build transcript text
        transcript_text = self._build_transcript_text(transcript_data)
        
        # Truncate if too long (keep ~15k chars for context)
        if len(transcript_text) > 15000:
            transcript_text = transcript_text[:15000] + "\n\n[Transcript truncated...]"
        
        # Build prompt
        prompt = self._build_prompt(transcript_text)
        
        # Call LLM API
        logger.info("Calling LLM API for summarization...")
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert meeting analyst. Always respond with valid JSON only."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"}
        )
        
        # Parse response
        response_text = response.choices[0].message.content
        
        try:
            summary_data = json.loads(response_text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response: {e}")
            # Fallback to basic structure
            summary_data = {
                "title": "Meeting Summary",
                "overview": response_text[:500],
                "key_points": [],
                "decisions": [],
                "discussion_topics": [],
                "next_steps": [],
                "participants": []
            }
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # Get duration from transcript metadata
        duration = transcript_data.get('metadata', {}).get('duration', 0)
        
        result = MeetingSummaryResult(
            title=summary_data.get('title', 'Meeting Summary'),
            overview=summary_data.get('overview', ''),
            key_points=summary_data.get('key_points', []),
            decisions=summary_data.get('decisions', []),
            discussion_topics=summary_data.get('discussion_topics', []),
            next_steps=summary_data.get('next_steps', []),
            participants=summary_data.get('participants', []),
            duration=duration,
            model=self.model,
            processing_time=processing_time,
            metadata={
                "source_file": transcript_data.get('metadata', {}).get('file', 'unknown'),
                "transcript_segments": len(transcript_data.get('transcript', []))
            }
        )
        
        logger.info(f"Summarization completed in {processing_time:.1f}s")
        return result
    
    def to_dict(self, result: MeetingSummaryResult) -> Dict:
        """Convert result to dictionary."""
        return {
            "status": "success",
            "title": result.title,
            "overview": result.overview,
            "key_points": result.key_points,
            "decisions": result.decisions,
            "discussion_topics": result.discussion_topics,
            "next_steps": result.next_steps,
            "participants": result.participants,
            "metadata": {
                "duration": result.duration,
                "model": result.model,
                "processing_time": result.processing_time,
                **result.metadata
            }
        }
    
    def to_markdown(self, result: MeetingSummaryResult) -> str:
        """Convert result to markdown format."""
        md = f"""# {result.title}

## 📋 Overview

{result.overview}

## 👥 Participants

"""
        if result.participants:
            for p in result.participants:
                md += f"- {p}\n"
        else:
            md += "*No participants identified*\n"
        
        md += "\n## 🔑 Key Points\n\n"
        if result.key_points:
            for point in result.key_points:
                md += f"- {point}\n"
        else:
            md += "*No key points identified*\n"
        
        md += "\n## 💡 Decisions Made\n\n"
        if result.decisions:
            for decision in result.decisions:
                md += f"- {decision}\n"
        else:
            md += "*No decisions recorded*\n"
        
        md += "\n## 📝 Discussion Topics\n\n"
        if result.discussion_topics:
            for topic in result.discussion_topics:
                topic_name = topic.get('topic', 'Topic')
                topic_summary = topic.get('summary', '')
                md += f"### {topic_name}\n\n{topic_summary}\n\n"
        else:
            md += "*No specific topics identified*\n"
        
        md += "\n## ➡️ Next Steps\n\n"
        if result.next_steps:
            for i, step in enumerate(result.next_steps, 1):
                md += f"{i}. {step}\n"
        else:
            md += "*No next steps identified*\n"
        
        md += f"""
---

*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*  
*Model: {result.model}*  
*Processing time: {result.processing_time:.1f}s*
"""
        return md
    
    def save_json(self, result: MeetingSummaryResult, output_path: str) -> str:
        """Save result as JSON file."""
        from pathlib import Path
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(result), f, indent=2, ensure_ascii=False)
        
        logger.info(f"Summary saved to {output_path}")
        return str(output_path)
    
    def save_markdown(self, result: MeetingSummaryResult, output_path: str) -> str:
        """Save result as Markdown file."""
        from pathlib import Path
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(self.to_markdown(result))
        
        logger.info(f"Summary saved to {output_path}")
        return str(output_path)
    
    def summarize_and_save(
        self,
        transcript_data: Dict,
        output_dir: str,
        base_name: str,
        formats: List[str] = ["json", "md"]
    ) -> Dict[str, str]:
        """
        Summarize and save to multiple formats.
        
        Args:
            transcript_data: Transcript data dictionary
            output_dir: Output directory
            base_name: Base name for output files
            formats: List of formats ('json', 'md')
            
        Returns:
            Dictionary mapping format to output file path
        """
        from pathlib import Path
        
        result = self.summarize(transcript_data)
        output_path = Path(output_dir)
        
        saved_files = {}
        
        for fmt in formats:
            if fmt == 'json':
                path = self.save_json(result, output_path / f"{base_name}.json")
                saved_files['json'] = path
            elif fmt == 'md':
                path = self.save_markdown(result, output_path / f"{base_name}.md")
                saved_files['md'] = path
        
        return saved_files


# Convenience function
def summarize_meeting_llm(
    transcript_file_path: str = None,
    transcript_data: Dict = None,
    output_file: Optional[str] = None,
    output_format: str = "json",
    model: str = "llama-3.3-70b-versatile"
) -> Dict[str, Any]:
    """
    Summarize a meeting using cloud LLM.
    
    Args:
        transcript_file_path: Path to transcript JSON file
        transcript_data: Direct transcript data (alternative to file)
        output_file: Path to save output
        output_format: Output format ('json' or 'md')
        model: LLM model to use
        
    Returns:
        Summary result dictionary
    """
    # Load transcript if file path provided
    if transcript_data is None:
        if transcript_file_path is None:
            raise ValueError("Either transcript_file_path or transcript_data required")
        with open(transcript_file_path, 'r', encoding='utf-8') as f:
            transcript_data = json.load(f)
    
    summarizer = LLMSummarizer(model=model)
    result = summarizer.summarize(transcript_data)
    
    # Save if output file specified
    if output_file:
        if output_format == 'md':
            summarizer.save_markdown(result, output_file)
        else:
            summarizer.save_json(result, output_file)
    
    return summarizer.to_dict(result)
