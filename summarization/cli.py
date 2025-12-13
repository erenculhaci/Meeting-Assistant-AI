import argparse
import json
import os
import sys
import logging
from summarization.summarizer import summarize_meeting

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Meeting Assistant AI - Summarization Module")

    # Required arguments
    parser.add_argument(
        "input_file",
        help="Path to the transcript JSON file"
    )

    # Optional arguments
    parser.add_argument(
        "--model",
        default="facebook/bart-large-cnn",
        help="Name or path of the BART model to use (default: facebook/bart-large-cnn)"
    )
    parser.add_argument(
        "--output_format",
        choices=["json", "txt", "md"],
        default="json",
        help="Format for the output file (default: json)"
    )
    parser.add_argument(
        "--output_file",
        help="Path to save the output file (default: based on input filename)"
    )
    parser.add_argument(
        "--max_length",
        type=int,
        default=150,
        help="Maximum length of the abstractive summary (default: 150)"
    )
    parser.add_argument(
        "--min_length",
        type=int,
        default=30,
        help="Minimum length of the abstractive summary (default: 30)"
    )
    parser.add_argument(
        "--no_action_items",
        action="store_true",
        help="Disable extraction of action items"
    )
    parser.add_argument(
        "--output_dir",
        default="outputs/summarization",
        help="Directory to save the output files (default: outputs/summarization)"
    )

    args = parser.parse_args()

    # Validate input file
    if not os.path.exists(args.input_file):
        logger.error(f"Input file not found: {args.input_file}")
        return 1

    # Configure output path
    if args.output_file:
        output_path = args.output_file
    else:
        base_filename = os.path.splitext(os.path.basename(args.input_file))[0]
        output_path = os.path.join(
            args.output_dir,
            f"{base_filename}_summary.{args.output_format}"
        )

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    try:
        # Run summarization
        summary_results = summarize_meeting(
            transcript_file_path=args.input_file,
            model_name=args.model,
            output_format=args.output_format,
            output_file=output_path,
            extract_action_items=not args.no_action_items,
            summary_length={"max": args.max_length, "min": args.min_length}
        )

        logger.info(f"Summary saved to {output_path}")

        # Print brief summary to console
        print("\nSummary Statistics:")
        print(f"- Transcript duration: {summary_results['metadata']['duration']:.1f} seconds")
        print(f"- Number of speakers: {summary_results['metadata']['num_speakers']}")
        print(f"- Key topics identified: {len(summary_results['summary']['key_topics'])}")
        print(f"- Key quotes extracted: {len(summary_results['summary']['extractive'])}")
        if not args.no_action_items:
            print(f"- Action items identified: {len(summary_results['summary']['action_items'])}")

    except Exception as e:
        logger.error(f"Error during summarization: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())