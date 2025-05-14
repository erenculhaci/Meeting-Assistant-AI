"""
Core implementation of the meeting summarizer.
"""

import os
import json
import logging
from typing import Dict, List, Tuple, Any, Optional
import torch
from transformers import (
    BartForConditionalGeneration,
    BartTokenizer,
    pipeline
)
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MeetingSummarizer:
    """
    A class to generate summaries of meeting transcripts using
    both extractive and abstractive summarization techniques.
    """

    def __init__(self, model_path: str = "facebook/bart-large-cnn"):
        """
        Initialize the summarizer with a BART model.

        Args:
            model_path: Path to the fine-tuned BART model or model name
        """
        logger.info(f"Initializing MeetingSummarizer with model: {model_path}")

        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Using device: {self.device}")

        # Load tokenizer and model
        self.tokenizer = BartTokenizer.from_pretrained(model_path)
        self.model = BartForConditionalGeneration.from_pretrained(model_path).to(self.device)

        # Initialize summarization pipeline for abstractive summaries
        self.summarization_pipeline = pipeline(
            "summarization",
            model=model_path,
            tokenizer=self.tokenizer,
            device=0 if self.device == "cuda" else -1
        )

        logger.info("MeetingSummarizer initialized successfully")

    def _preprocess_transcript(self, transcript_data: Dict[str, Any]) -> Tuple[str, Dict[str, List[Dict[str, Any]]]]:
        """
        Preprocess the transcript data for summarization.

        Args:
            transcript_data: Transcript data in JSON format

        Returns:
            full_text: The complete transcript text
            speakers_utterances: Dictionary mapping speakers to their utterances
        """
        logger.info("Preprocessing transcript data")

        # Extract the transcript segments
        transcript_segments = transcript_data.get("transcript", [])

        # Get the full text
        full_text = transcript_data.get("full_text", "")
        if not full_text and transcript_segments:
            full_text = " ".join([segment.get("text", "") for segment in transcript_segments])

        # Group utterances by speaker
        speakers_utterances = {}
        for segment in transcript_segments:
            speaker = segment.get("speaker", "Unknown")
            if speaker not in speakers_utterances:
                speakers_utterances[speaker] = []

            speakers_utterances[speaker].append({
                "text": segment.get("text", ""),
                "start": segment.get("start", 0),
                "end": segment.get("end", 0)
            })

        return full_text, speakers_utterances

    def _generate_extractive_summary(self, transcript_segments: List[Dict[str, Any]], n_sentences: int = 5) -> List[Dict[str, Any]]:
        """
        Generate an extractive summary by selecting the most important sentences.

        Args:
            transcript_segments: List of transcript segments
            n_sentences: Number of sentences to extract

        Returns:
            List of important segments with their metadata
        """
        logger.info(f"Generating extractive summary with {n_sentences} sentences")

        # Filter out segments from the instruction speaker (typically Speaker_00)
        content_segments = [seg for seg in transcript_segments
                            if seg.get("speaker") not in ["Speaker_00", "Unknown"]]

        if not content_segments:
            logger.warning("No content segments found for extractive summary")
            return []

        # Extract text from segments
        sentences = [seg.get("text", "") for seg in content_segments]

        if len(sentences) <= n_sentences:
            logger.info(f"Few segments ({len(sentences)}), returning all")
            return content_segments

        # Use TF-IDF and cosine similarity to find important sentences
        vectorizer = TfidfVectorizer(stop_words='english')
        try:
            # Create TF-IDF matrix
            tfidf_matrix = vectorizer.fit_transform(sentences)

            # Calculate similarity between sentences
            similarity_matrix = cosine_similarity(tfidf_matrix)

            # Calculate sentence scores
            scores = np.sum(similarity_matrix, axis=1)

            # Get indices of top sentences
            top_indices = np.argsort(scores)[-n_sentences:]

            # Sort indices by their position in the original text
            top_indices = sorted(top_indices)

            # Return the top segments with their metadata
            important_segments = [content_segments[i] for i in top_indices]
            return important_segments

        except Exception as e:
            logger.error(f"Error in extractive summarization: {e}")
            return content_segments[:n_sentences]

    def _generate_abstractive_summary(self, text: str, max_length: int = 150, min_length: int = 30) -> str:
        """
        Generate an abstractive summary of the text using the BART model.

        Args:
            text: Text to summarize
            max_length: Maximum summary length
            min_length: Minimum summary length

        Returns:
            Abstractive summary
        """
        logger.info("Generating abstractive summary")

        # Check if text is too short
        if len(text.split()) < 30:
            logger.info("Text too short for abstractive summary")
            return text

        try:
            summary = self.summarization_pipeline(
                text,
                max_length=max_length,
                min_length=min_length,
                do_sample=False
            )

            return summary[0]['summary_text']

        except Exception as e:
            logger.error(f"Error in abstractive summarization: {e}")
            return f"Failed to generate abstractive summary: {str(e)}"

    def _generate_abstractive_summary_for_long_text(self, text: str, max_length: int = 150,
                                                    min_length: int = 30) -> str:
        """
        Generate an abstractive summary of long text by chunking and summarizing iteratively.

        Args:
            text: Long text to summarize
            max_length: Maximum final summary length
            min_length: Minimum final summary length

        Returns:
            Abstractive summary of the entire text
        """
        logger.info("Generating abstractive summary for long text using chunking approach")

        # Check if text is too short for chunking
        if len(text.split()) < 500:  # If text is short enough, use regular summary
            return self._generate_abstractive_summary(text, max_length, min_length)

        # Constants for chunking
        max_chunk_tokens = 1000  # Slightly smaller than model's limit for safety
        chunk_overlap = 100  # Number of tokens to overlap between chunks

        try:
            # Tokenize the full text
            tokens = self.tokenizer(text, return_tensors="pt", truncation=False)
            input_ids = tokens["input_ids"][0]
            full_length = len(input_ids)

            logger.info(f"Processing long input ({full_length} tokens) with chunking approach")

            # Calculate number of chunks needed
            effective_chunk_size = max_chunk_tokens - chunk_overlap
            num_chunks = (full_length + effective_chunk_size - 1) // effective_chunk_size

            # Initialize intermediate summaries list
            intermediate_summaries = []

            # Process each chunk
            for i in range(num_chunks):
                start_idx = i * effective_chunk_size
                end_idx = min(start_idx + max_chunk_tokens, full_length)

                # Get chunk text
                chunk_tokens = input_ids[start_idx:end_idx]
                chunk_text = self.tokenizer.decode(chunk_tokens, skip_special_tokens=True)

                logger.info(f"Processing chunk {i + 1}/{num_chunks} ({len(chunk_tokens)} tokens)")

                # Generate summary for this chunk
                chunk_summary = self._generate_abstractive_summary(
                    chunk_text,
                    max_length=max(30, max_length // 2),  # Shorter intermediate summaries
                    min_length=min(15, min_length // 2)
                )

                intermediate_summaries.append(chunk_summary)

            # Combine intermediate summaries
            combined_text = " ".join(intermediate_summaries)

            # Final summarization pass
            logger.info(f"Generating final summary from {len(intermediate_summaries)} intermediate summaries")
            final_summary = self._generate_abstractive_summary(
                combined_text,
                max_length=max_length,
                min_length=min_length
            )

            return final_summary

        except Exception as e:
            logger.error(f"Error in chunked abstractive summarization: {e}")
            logger.warning("Falling back to extractive summarization due to error")
            return "Failed to generate abstractive summary. Please check the extractive summary instead."

    def _identify_key_topics(self, text: str, num_topics: int = 5) -> List[str]:
        """
        Identify key topics in the transcript using TF-IDF.

        Args:
            text: The transcript text
            num_topics: Number of topics to identify

        Returns:
            List of key topics
        """
        logger.info(f"Identifying {num_topics} key topics")

        try:
            # Tokenize into sentences
            sentences = [s.strip() for s in text.split('.') if len(s.strip()) > 0]

            # Use TF-IDF to identify important terms
            vectorizer = TfidfVectorizer(
                max_df=0.9, min_df=2, stop_words='english',
                max_features=200, ngram_range=(1, 2)
            )

            tfidf_matrix = vectorizer.fit_transform(sentences)
            feature_names = vectorizer.get_feature_names_out()

            # Sum TF-IDF scores for each term across all sentences
            scores = np.asarray(tfidf_matrix.sum(axis=0)).flatten()

            # Get top terms
            top_indices = scores.argsort()[-num_topics:][::-1]
            topics = [feature_names[i].title() for i in top_indices]

            return topics

        except Exception as e:
            logger.error(f"Error identifying topics: {e}")
            return []

    def _extract_action_items(self, transcript_segments: List[Dict[str, Any]]) -> List[str]:
        """
        Extract potential action items from the transcript.

        Args:
            transcript_segments: List of transcript segments

        Returns:
            List of potential action items
        """
        logger.info("Extracting action items")

        action_items = []
        action_indicators = [
            "need to", "should", "will", "going to",
            "have to", "must", "let's", "task", "action item",
            "follow up", "get back to", "take care of"
        ]

        for segment in transcript_segments:
            text = segment.get("text", "").lower()
            speaker = segment.get("speaker", "")

            # Skip instructional or unknown speakers
            if speaker in ["Speaker_00", "Unknown"]:
                continue

            # Check if the segment contains action indicators
            if any(indicator in text for indicator in action_indicators):
                # Clean up the text a bit
                item = segment.get("text", "").strip()

                # Add speaker information
                action_items.append(f"{speaker}: {item}")

        return action_items

    def summarize(
            self, transcript_data: Dict[str, Any],
            include_action_items: bool = True,
            max_summary_length: int = 150,
            min_summary_length: int = 30,
            num_extractive_sentences: int = 5
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive summary of the meeting.

        Args:
            transcript_data: Transcript data in JSON format
            include_action_items: Whether to extract action items
            max_summary_length: Maximum length of the abstractive summary
            min_summary_length: Minimum length of the abstractive summary
            num_extractive_sentences: Number of sentences to include in extractive summary

        Returns:
            Dictionary containing various summary components
        """
        logger.info("Starting summarization process")

        # Preprocess transcript
        full_text, speakers_utterances = self._preprocess_transcript(transcript_data)

        # Extract metadata
        metadata = transcript_data.get("metadata", {})

        # Get transcript segments
        transcript_segments = transcript_data.get("transcript", [])

        # Generate abstractive summary using the chunking approach for long text
        abstractive_summary = self._generate_abstractive_summary_for_long_text(
            full_text,
            max_length=max_summary_length,
            min_length=min_summary_length
        )

        # Generate extractive summary
        extractive_segments = self._generate_extractive_summary(
            transcript_segments,
            n_sentences=num_extractive_sentences
        )
        extractive_summary = [seg.get("text", "") for seg in extractive_segments]

        # Identify key topics
        key_topics = self._identify_key_topics(full_text)

        # Extract action items if requested
        action_items = []
        if include_action_items:
            action_items = self._extract_action_items(transcript_segments)

        # Prepare speaker statistics
        speaker_stats = {}
        for speaker, utterances in speakers_utterances.items():
            # Skip instructional or unknown speakers
            if speaker in ["Speaker_00", "Unknown"]:
                continue

            # Calculate speaking time
            speaking_time = sum(utt.get("end", 0) - utt.get("start", 0) for utt in utterances)

            # Count utterances
            num_utterances = len(utterances)

            # Calculate average utterance length
            total_words = sum(len(utt.get("text", "").split()) for utt in utterances)
            avg_words = total_words / num_utterances if num_utterances > 0 else 0

            speaker_stats[speaker] = {
                "speaking_time": speaking_time,
                "utterances": num_utterances,
                "avg_words_per_utterance": avg_words,
                "total_words": total_words
            }

        # Prepare summary results
        summary_results = {
            "metadata": {
                "original_metadata": metadata,
                "summary_generated": "yes",
                "duration": metadata.get("duration", 0),
                "language": metadata.get("language", "en"),
                "num_speakers": len([s for s in speakers_utterances.keys() if s not in ["Speaker_00", "Unknown"]])
            },
            "summary": {
                "abstractive": abstractive_summary,
                "extractive": extractive_summary,
                "key_topics": key_topics,
                "action_items": action_items
            },
            "speaker_stats": speaker_stats
        }

        logger.info("Summarization completed successfully")
        return summary_results

    def save_summary(self, summary_results: Dict[str, Any], output_path: str) -> None:
        """
        Save the summary results to a JSON file.

        Args:
            summary_results: Summary results dictionary
            output_path: Path to save the summary
        """
        logger.info(f"Saving summary to {output_path}")

        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # Write the summary to file
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(summary_results, f, indent=2, ensure_ascii=False)

            logger.info(f"Summary saved successfully to {output_path}")

        except Exception as e:
            logger.error(f"Error saving summary: {e}")

    def save_text_summary(self, summary_results: Dict[str, Any], output_path: str) -> None:
        """
        Save the summary results as a plain text file.

        Args:
            summary_results: Summary results dictionary
            output_path: Path to save the text summary
        """
        logger.info(f"Saving text summary to {output_path}")

        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("=== MEETING SUMMARY ===\n\n")

                # Write abstractive summary
                f.write("OVERVIEW:\n")
                f.write(summary_results["summary"]["abstractive"])
                f.write("\n\n")

                # Write key topics
                f.write("KEY TOPICS:\n")
                for i, topic in enumerate(summary_results["summary"]["key_topics"], 1):
                    f.write(f"{i}. {topic}\n")
                f.write("\n")

                # Write key quotes (extractive)
                f.write("KEY QUOTES:\n")
                for quote in summary_results["summary"]["extractive"]:
                    f.write(f"- {quote}\n")
                f.write("\n")

                # Write action items if any
                if summary_results["summary"]["action_items"]:
                    f.write("ACTION ITEMS:\n")
                    for item in summary_results["summary"]["action_items"]:
                        f.write(f"- {item}\n")
                    f.write("\n")

                # Write speaker statistics
                f.write("SPEAKER STATISTICS:\n")
                for speaker, stats in summary_results["speaker_stats"].items():
                    f.write(f"- {speaker}:\n")
                    f.write(f"  Speaking time: {stats['speaking_time']:.1f} seconds\n")
                    f.write(f"  Utterances: {stats['utterances']}\n")
                    f.write(f"  Words: {stats['total_words']}\n")

                # Write metadata
                f.write("\n=== METADATA ===\n")
                f.write(f"Duration: {summary_results['metadata']['duration']:.1f} seconds\n")
                f.write(f"Language: {summary_results['metadata']['language']}\n")
                f.write(f"Number of participants: {summary_results['metadata']['num_speakers']}\n")

            logger.info(f"Text summary saved successfully to {output_path}")

        except Exception as e:
            logger.error(f"Error saving text summary: {e}")

    def save_markdown_summary(self, summary_results: Dict[str, Any], output_path: str) -> None:
        """
        Save the summary results as a markdown file.

        Args:
            summary_results: Summary results dictionary
            output_path: Path to save the markdown summary
        """
        logger.info(f"Saving markdown summary to {output_path}")

        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("# Meeting Summary\n\n")

                # Write abstractive summary
                f.write("## Overview\n\n")
                f.write(summary_results["summary"]["abstractive"])
                f.write("\n\n")

                # Write key topics
                f.write("## Key Topics\n\n")
                for topic in summary_results["summary"]["key_topics"]:
                    f.write(f"- {topic}\n")
                f.write("\n")

                # Write key quotes (extractive)
                f.write("## Key Quotes\n\n")
                for quote in summary_results["summary"]["extractive"]:
                    f.write(f"> {quote}\n\n")

                # Write action items if any
                if summary_results["summary"]["action_items"]:
                    f.write("## Action Items\n\n")
                    for item in summary_results["summary"]["action_items"]:
                        f.write(f"- [ ] {item}\n")
                    f.write("\n")

                # Write speaker statistics
                f.write("## Speaker Statistics\n\n")
                f.write("| Speaker | Speaking Time (s) | Utterances | Total Words | Avg Words/Utterance |\n")
                f.write("|---------|------------------|------------|-------------|---------------------|\n")
                for speaker, stats in summary_results["speaker_stats"].items():
                    f.write(f"| {speaker} | {stats['speaking_time']:.1f} | {stats['utterances']} | {stats['total_words']} | {stats['avg_words_per_utterance']:.1f} |\n")

                # Write metadata
                f.write("\n## Metadata\n\n")
                f.write(f"- **Duration**: {summary_results['metadata']['duration']:.1f} seconds\n")
                f.write(f"- **Language**: {summary_results['metadata']['language']}\n")
                f.write(f"- **Number of participants**: {summary_results['metadata']['num_speakers']}\n")

            logger.info(f"Markdown summary saved successfully to {output_path}")

        except Exception as e:
            logger.error(f"Error saving markdown summary: {e}")