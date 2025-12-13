import json
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .transcriber import TranscriptionResult


class BaseFormatter(ABC):
    
    @abstractmethod
    def format(self, result: "TranscriptionResult") -> str:
        pass


class JSONFormatter(BaseFormatter):
    
    def format(self, result: "TranscriptionResult") -> str:
        output = {
            "status": "success",
            "metadata": {
                "file": result.source_file,
                "duration": result.duration,
                "model": result.model,
                "language": result.language,
                "processing_time": result.processing_time,
                "include_timestamps": result.metadata.get("include_timestamps", True)
            },
            "transcript": [
                {
                    "text": segment.text,
                    "speaker": segment.speaker,
                    "start": segment.start,
                    "end": segment.end
                }
                for segment in result.segments
            ]
        }
        
        return json.dumps(output, indent=2, ensure_ascii=False)


class SRTFormatter(BaseFormatter):
    def _format_timestamp(self, seconds: float) -> str:
        """Convert seconds to SRT timestamp format HH:MM:SS,mmm"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
    
    def format(self, result: "TranscriptionResult") -> str:
        lines = []
        
        for i, segment in enumerate(result.segments, 1):
            start_time = self._format_timestamp(segment.start)
            end_time = self._format_timestamp(segment.end)
            
            speaker_prefix = f"[{segment.speaker}] " if segment.speaker else ""
            
            lines.append(str(i))
            lines.append(f"{start_time} --> {end_time}")
            lines.append(f"{speaker_prefix} {segment.text}")
            lines.append("")  # Empty line between entries
        
        return "\n".join(lines)


class VTTFormatter(BaseFormatter):
    def _format_timestamp(self, seconds: float) -> str:
        """Convert seconds to VTT timestamp format HH:MM:SS.mmm"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"
    
    def format(self, result: "TranscriptionResult") -> str:
        lines = ["WEBVTT", ""]  # Header
        
        for i, segment in enumerate(result.segments, 1):
            start_time = self._format_timestamp(segment.start)
            end_time = self._format_timestamp(segment.end)
            
            speaker_prefix = f"<v {segment.speaker}>" if segment.speaker else ""
            
            lines.append(str(i))
            lines.append(f"{start_time} --> {end_time}")
            lines.append(f"{speaker_prefix}{segment.text}")
            lines.append("")
        
        return "\n".join(lines)


class TXTFormatter(BaseFormatter):
    
    def __init__(self, include_speakers: bool = True, include_timestamps: bool = False):
        self.include_speakers = include_speakers
        self.include_timestamps = include_timestamps
    
    def _format_timestamp(self, seconds: float) -> str:
        """Convert seconds to readable format MM:SS"""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"[{minutes:02d}:{secs:02d}]"
    
    def format(self, result: "TranscriptionResult") -> str:
        lines = []
        
        # Add header with metadata
        lines.append(f"Transcription: {result.source_file}")
        lines.append(f"Duration: {result.duration:.1f} seconds")
        lines.append(f"Language: {result.language}")
        lines.append("-" * 50)
        lines.append("")
        
        current_speaker = None
        
        for segment in result.segments:
            parts = []
            
            # Add timestamp if enabled
            if self.include_timestamps:
                parts.append(self._format_timestamp(segment.start))
            
            # Add speaker if changed and enabled
            if self.include_speakers and segment.speaker:
                if segment.speaker != current_speaker:
                    current_speaker = segment.speaker
                    parts.append(f"\n{segment.speaker}:")
            
            parts.append(segment.text)
            
            lines.append(" ".join(parts))
        
        return "\n".join(lines)
