"""
Main Transcriber class for audio/video transcription
Uses Groq Whisper API for fast and accurate transcription (free tier available)
"""

import os
import time
from pathlib import Path
from typing import Optional, List, Dict, Any, Literal
from dataclasses import dataclass, field
from groq import Groq
from pydub import AudioSegment
import tempfile
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from .formatters import JSONFormatter, SRTFormatter, TXTFormatter, VTTFormatter


@dataclass
class TranscriptSegment:
    """Represents a single segment of transcription"""
    text: str
    start: float
    end: float
    speaker: Optional[str] = None


@dataclass
class TranscriptionResult:
    """Complete transcription result with metadata"""
    segments: List[TranscriptSegment]
    full_text: str
    duration: float
    language: str
    model: str
    processing_time: float
    source_file: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class Transcriber:
    """
    Audio/Video Transcription class
    
    Supported input formats:
    - Audio: MP3, WAV, M4A, OGG, FLAC, WEBM, AAC
    - Video: MP4, MKV, AVI, MOV, WEBM
    
    Output formats:
    - JSON: Detailed transcription with timestamps and speaker info
    - SRT: Standard subtitle format
    - VTT: Web Video Text Tracks format
    - TXT: Plain text transcription
    """
    
    SUPPORTED_AUDIO_FORMATS = {'.mp3', '.wav', '.m4a', '.ogg', '.flac', '.webm', '.aac'}
    SUPPORTED_VIDEO_FORMATS = {'.mp4', '.mkv', '.avi', '.mov', '.webm'}
    
    # Whisper API max file size is 25MB
    MAX_FILE_SIZE = 25 * 1024 * 1024
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Transcriber
        
        Args:
            api_key: Groq API key. If not provided, uses GROQ_API_KEY env variable
        """
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Groq API key required. Provide via api_key parameter or "
                "set GROQ_API_KEY environment variable."
            )
        
        self.client = Groq(api_key=self.api_key)
        self.formatters = {
            'json': JSONFormatter(),
            'srt': SRTFormatter(),
            'vtt': VTTFormatter(),
            'txt': TXTFormatter()
        }
    
    def _extract_audio(self, input_path: Path) -> Path:
        """
        Extract audio from video file or convert audio to suitable format
        
        Args:
            input_path: Path to input file
            
        Returns:
            Path to temporary audio file in MP3 format
        """
        suffix = input_path.suffix.lower()
        
        # Load audio using pydub
        if suffix in self.SUPPORTED_VIDEO_FORMATS:
            # For video files, extract audio
            audio = AudioSegment.from_file(str(input_path))
        elif suffix == '.wav':
            audio = AudioSegment.from_wav(str(input_path))
        elif suffix == '.mp3':
            audio = AudioSegment.from_mp3(str(input_path))
        elif suffix == '.ogg':
            audio = AudioSegment.from_ogg(str(input_path))
        elif suffix == '.flac':
            audio = AudioSegment.from_file(str(input_path), format="flac")
        else:
            audio = AudioSegment.from_file(str(input_path))
        
        # Create temp file
        temp_file = tempfile.NamedTemporaryFile(suffix='.mp3', delete=False)
        temp_path = Path(temp_file.name)
        temp_file.close()
        
        # Export as MP3 with reasonable quality for speech
        audio.export(str(temp_path), format='mp3', bitrate='64k')
        
        return temp_path
    
    def _split_audio(self, audio_path: Path, chunk_duration_ms: int = 600000) -> List[Path]:
        """
        Split audio into chunks if file is too large
        
        Args:
            audio_path: Path to audio file
            chunk_duration_ms: Duration of each chunk in milliseconds (default 10 minutes)
            
        Returns:
            List of paths to chunk files
        """
        audio = AudioSegment.from_mp3(str(audio_path))
        duration_ms = len(audio)
        
        if duration_ms <= chunk_duration_ms:
            return [audio_path]
        
        chunks = []
        for i, start in enumerate(range(0, duration_ms, chunk_duration_ms)):
            end = min(start + chunk_duration_ms, duration_ms)
            chunk = audio[start:end]
            
            temp_file = tempfile.NamedTemporaryFile(suffix=f'_chunk{i}.mp3', delete=False)
            temp_path = Path(temp_file.name)
            temp_file.close()
            
            chunk.export(str(temp_path), format='mp3', bitrate='64k')
            chunks.append((temp_path, start / 1000))  # Store path and start time in seconds
        
        return chunks
    
    def transcribe(
        self,
        input_path: str,
        language: Optional[str] = None,
        detect_speakers: bool = True,
        model: Literal["whisper-large-v3", "whisper-large-v3-turbo", "distil-whisper-large-v3-en"] = "whisper-large-v3-turbo",
        prompt: Optional[str] = None,
        response_format: Literal["verbose_json"] = "verbose_json"
    ) -> TranscriptionResult:
        """
        Transcribe an audio or video file
        
        Args:
            input_path: Path to input audio/video file
            language: Language code (e.g., 'en', 'tr'). Auto-detected if not provided
            detect_speakers: Enable speaker detection/diarization (basic)
            model: Whisper model to use
            prompt: Optional prompt to guide transcription style
            response_format: Response format from API
            
        Returns:
            TranscriptionResult object containing all transcription data
        """
        start_time = time.time()
        input_path = Path(input_path)
        
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")
        
        suffix = input_path.suffix.lower()
        if suffix not in self.SUPPORTED_AUDIO_FORMATS | self.SUPPORTED_VIDEO_FORMATS:
            raise ValueError(
                f"Unsupported format: {suffix}. "
                f"Supported: {self.SUPPORTED_AUDIO_FORMATS | self.SUPPORTED_VIDEO_FORMATS}"
            )
        
        # Extract/convert audio
        temp_audio_path = self._extract_audio(input_path)
        
        try:
            # Get audio duration
            audio = AudioSegment.from_mp3(str(temp_audio_path))
            duration_seconds = len(audio) / 1000
            
            # Check file size and split if necessary
            file_size = temp_audio_path.stat().st_size
            
            all_segments = []
            detected_language = language
            
            if file_size > self.MAX_FILE_SIZE:
                # Split into chunks
                chunks = self._split_audio(temp_audio_path)
                
                for chunk_path, chunk_start in chunks:
                    try:
                        with open(chunk_path, 'rb') as audio_file:
                            response = self.client.audio.transcriptions.create(
                                model=model,
                                file=audio_file,
                                language=language,
                                prompt=prompt,
                                response_format=response_format
                            )
                        
                        if not detected_language and hasattr(response, 'language'):
                            detected_language = response.language
                        
                        # Adjust timestamps for chunk offset
                        # Groq returns segments as dicts or objects
                        for segment in response.segments:
                            if isinstance(segment, dict):
                                text = segment.get('text', '').strip()
                                start = segment.get('start', 0)
                                end = segment.get('end', 0)
                            else:
                                text = segment.text.strip()
                                start = segment.start
                                end = segment.end
                            
                            all_segments.append(TranscriptSegment(
                                text=text,
                                start=start + chunk_start,
                                end=end + chunk_start,
                                speaker=None
                            ))
                    finally:
                        if chunk_path != temp_audio_path:
                            os.unlink(chunk_path)
            else:
                # Single file transcription
                with open(temp_audio_path, 'rb') as audio_file:
                    response = self.client.audio.transcriptions.create(
                        model=model,
                        file=audio_file,
                        language=language,
                        prompt=prompt,
                        response_format=response_format
                    )
                
                detected_language = getattr(response, 'language', language or 'unknown')
                
                # Groq returns segments as dicts or objects
                for segment in response.segments:
                    if isinstance(segment, dict):
                        text = segment.get('text', '').strip()
                        start = segment.get('start', 0)
                        end = segment.get('end', 0)
                    else:
                        text = segment.text.strip()
                        start = segment.start
                        end = segment.end
                    
                    all_segments.append(TranscriptSegment(
                        text=text,
                        start=start,
                        end=end,
                        speaker=None
                    ))
            
            # Basic speaker detection (based on pauses and text patterns)
            if detect_speakers:
                all_segments = self._detect_speakers(all_segments)
            
            processing_time = time.time() - start_time
            
            return TranscriptionResult(
                segments=all_segments,
                full_text=" ".join(s.text for s in all_segments),
                duration=duration_seconds,
                language=detected_language or 'unknown',
                model=model,
                processing_time=processing_time,
                source_file=input_path.name,
                metadata={
                    "include_timestamps": True,
                    "speaker_detection": detect_speakers
                }
            )
            
        finally:
            # Cleanup temp file
            if temp_audio_path.exists():
                os.unlink(temp_audio_path)
    
    def _detect_speakers(self, segments: List[TranscriptSegment]) -> List[TranscriptSegment]:
        """
        Basic speaker detection based on pauses between segments
        This is a simple heuristic - for better results, use a dedicated
        speaker diarization service
        """
        if not segments:
            return segments
        
        current_speaker = 0
        speaker_map = {}
        
        for i, segment in enumerate(segments):
            if i == 0:
                segments[i].speaker = f"Speaker_{current_speaker:02d}"
                continue
            
            prev_segment = segments[i - 1]
            gap = segment.start - prev_segment.end
            
            # If there's a significant pause (>1.5 seconds), might be speaker change
            if gap > 1.5:
                # Simple alternation logic
                current_speaker = (current_speaker + 1) % 3
            
            segments[i].speaker = f"Speaker_{current_speaker:02d}"
        
        return segments
    
    def save(
        self,
        result: TranscriptionResult,
        output_path: str,
        format: Literal["json", "srt", "vtt", "txt"] = "json"
    ) -> str:
        """
        Save transcription result to file
        
        Args:
            result: TranscriptionResult to save
            output_path: Path for output file (extension will be added if missing)
            format: Output format ('json', 'srt', 'vtt', 'txt')
            
        Returns:
            Path to saved file
        """
        if format not in self.formatters:
            raise ValueError(f"Unknown format: {format}. Supported: {list(self.formatters.keys())}")
        
        formatter = self.formatters[format]
        output_path = Path(output_path)
        
        # Add extension if not present
        expected_ext = f".{format}"
        if output_path.suffix.lower() != expected_ext:
            output_path = output_path.with_suffix(expected_ext)
        
        # Create output directory if needed
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Format and save
        formatted_content = formatter.format(result)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(formatted_content)
        
        return str(output_path)
    
    def transcribe_and_save(
        self,
        input_path: str,
        output_dir: str,
        formats: List[str] = ["json", "srt"],
        language: Optional[str] = None,
        detect_speakers: bool = True
    ) -> Dict[str, str]:
        """
        Transcribe and save to multiple formats in one call
        
        Args:
            input_path: Path to input audio/video file
            output_dir: Directory for output files
            formats: List of output formats
            language: Language code
            detect_speakers: Enable speaker detection
            
        Returns:
            Dictionary mapping format to output file path
        """
        result = self.transcribe(
            input_path=input_path,
            language=language,
            detect_speakers=detect_speakers
        )
        
        output_dir = Path(output_dir)
        base_name = Path(input_path).stem
        
        saved_files = {}
        for fmt in formats:
            output_path = output_dir / f"{base_name}.{fmt}"
            saved_path = self.save(result, str(output_path), fmt)
            saved_files[fmt] = saved_path
        
        return saved_files
