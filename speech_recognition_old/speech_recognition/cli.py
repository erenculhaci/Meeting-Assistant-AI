"""
Command-line interface for the transcriber module
Usage: python -m transcriber input_file [options]
"""

import argparse
import sys
from pathlib import Path
from .transcriber import Transcriber


def main():
    parser = argparse.ArgumentParser(
        description="Transcribe audio/video files to text with timestamps",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m transcriber video.mp4
  python -m transcriber audio.mp3 -o ./output -f json srt
  python -m transcriber meeting.wav -l tr -f json srt vtt txt

Supported input formats:
  Audio: MP3, WAV, M4A, OGG, FLAC, WEBM, AAC
  Video: MP4, MKV, AVI, MOV, WEBM

Output formats:
  json - Full transcription with metadata and timestamps
  srt  - Standard subtitle format
  vtt  - Web Video Text Tracks format
  txt  - Plain text transcription
        """
    )
    
    parser.add_argument(
        "input",
        help="Path to audio or video file to transcribe"
    )
    
    parser.add_argument(
        "-o", "--output",
        default=".",
        help="Output directory (default: current directory)"
    )
    
    parser.add_argument(
        "-f", "--formats",
        nargs="+",
        default=["json", "srt"],
        choices=["json", "srt", "vtt", "txt"],
        help="Output formats (default: json srt)"
    )
    
    parser.add_argument(
        "-l", "--language",
        default=None,
        help="Language code (e.g., en, tr). Auto-detected if not specified"
    )
    
    parser.add_argument(
        "--no-speakers",
        action="store_true",
        help="Disable speaker detection"
    )
    
    parser.add_argument(
        "-k", "--api-key",
        default=None,
        help="OpenAI API key (or set OPENAI_API_KEY env variable)"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Show detailed progress information"
    )
    
    args = parser.parse_args()
    
    # Validate input file
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)
    
    # Create output directory
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        if args.verbose:
            print(f"Initializing transcriber...")
        
        transcriber = Transcriber(api_key=args.api_key)
        
        if args.verbose:
            print(f"Transcribing: {input_path}")
            print(f"Language: {args.language or 'auto-detect'}")
            print(f"Speaker detection: {'disabled' if args.no_speakers else 'enabled'}")
        
        # Transcribe
        result = transcriber.transcribe(
            input_path=str(input_path),
            language=args.language,
            detect_speakers=not args.no_speakers
        )
        
        if args.verbose:
            print(f"\nTranscription completed!")
            print(f"Duration: {result.duration:.1f} seconds")
            print(f"Language: {result.language}")
            print(f"Processing time: {result.processing_time:.1f} seconds")
            print(f"Segments: {len(result.segments)}")
        
        # Save to all requested formats
        print(f"\nSaving output files:")
        for fmt in args.formats:
            output_path = output_dir / f"{input_path.stem}.{fmt}"
            saved_path = transcriber.save(result, str(output_path), fmt)
            print(f"  {fmt.upper()}: {saved_path}")
        
        print("\nDone!")
        
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error during transcription: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
