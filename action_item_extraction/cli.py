"""
Command-line interface for action item extraction.
"""

import argparse
import sys
import logging
from datetime import datetime

from action_item_extraction.extractor import extract_action_items

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Command-line interface for action item extraction."""
    parser = argparse.ArgumentParser(
        description="Extract action items and tasks from meeting transcripts"
    )
    
    # Required arguments
    parser.add_argument(
        "input_file",
        help="Path to the transcript JSON file"
    )
    
    # Optional arguments
    parser.add_argument(
        "--output_file",
        help="Path to save the output file (default: based on input filename)"
    )
    parser.add_argument(
        "--output_format",
        choices=["json", "md", "txt"],
        default="md",
        help="Format for the output file (default: md)"
    )
    parser.add_argument(
        "--reference_date",
        help="Reference date for relative date parsing (format: YYYY-MM-DD)"
    )
    parser.add_argument(
        "--output_dir",
        default="outputs/action_items",
        help="Directory to save the output files (default: outputs/action_items)"
    )
    
    args = parser.parse_args()
    
    # Parse reference date if provided
    reference_date = None
    if args.reference_date:
        try:
            reference_date = datetime.strptime(args.reference_date, '%Y-%m-%d')
        except ValueError:
            logger.error(f"Invalid date format: {args.reference_date}. Use YYYY-MM-DD")
            return 1
    
    # Configure output path
    if args.output_file:
        output_path = args.output_file
    else:
        import os
        base_filename = os.path.splitext(os.path.basename(args.input_file))[0]
        output_path = os.path.join(
            args.output_dir,
            f"{base_filename}_action_items.{args.output_format}"
        )
    
    try:
        # Extract action items
        tasks = extract_action_items(
            transcript_file_path=args.input_file,
            output_file=output_path,
            output_format=args.output_format,
            reference_date=reference_date
        )
        
        logger.info(f"Action items saved to {output_path}")
        
        # Print summary
        print("\n" + "="*60)
        print("ACTION ITEMS EXTRACTION SUMMARY")
        print("="*60)
        print(f"Total tasks extracted: {len(tasks)}")
        
        if tasks:
            high = len([t for t in tasks if t['priority'] == 'high'])
            medium = len([t for t in tasks if t['priority'] == 'medium'])
            low = len([t for t in tasks if t['priority'] == 'low'])
            
            print(f"\nBy Priority:")
            print(f"  - High: {high}")
            print(f"  - Medium: {medium}")
            print(f"  - Low: {low}")
            
            assigned = len([t for t in tasks if t['assignee'] != 'Unassigned'])
            print(f"\nAssigned tasks: {assigned}/{len(tasks)}")
            
            with_deadlines = len([t for t in tasks if t.get('due_date')])
            print(f"Tasks with deadlines: {with_deadlines}/{len(tasks)}")
            
            print(f"\nOutput saved to: {output_path}")
        
        print("="*60 + "\n")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error during extraction: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
