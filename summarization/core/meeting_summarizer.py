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
import re
from collections import Counter

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MeetingSummarizer:

    def __init__(self, model_path: str = "facebook/bart-large-cnn"):
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

    def _clean_summary_text(self, text: str) -> str:
        if not text:
            return text
            
        # Remove excessive quotes and fix formatting
        text = re.sub(r'"\s*"', '', text)  # Remove empty quotes
        text = re.sub(r'\s+', ' ', text)   # Normalize whitespace
        
        # Remove sentences that are just filler or too short
        sentences = re.split(r'[.!?]+', text)
        cleaned_sentences = []
        
        filler_starters = ['like', 'yeah', 'um', 'uh', 'so', 'well', 'i mean', 'you know']
        
        for sentence in sentences:
            sentence = sentence.strip()
            
            # Skip very short sentences
            if len(sentence.split()) < 4:
                continue
                
            # Skip if starts with filler
            if any(sentence.lower().startswith(filler) for filler in filler_starters):
                continue
            
            # Skip if mostly filler words
            words = sentence.lower().split()
            filler_count = sum(1 for word in words if word in ['like', 'yeah', 'um', 'uh', 'just', 'really', 'kind', 'sort', 'thing'])
            if len(words) > 0 and filler_count / len(words) > 0.3:
                continue
                
            cleaned_sentences.append(sentence)
        
        # Rejoin sentences
        result = '. '.join(cleaned_sentences)
        if result and not result.endswith('.'):
            result += '.'
            
        return result

    def _preprocess_transcript(self, transcript_data: Dict[str, Any]) -> Tuple[str, Dict[str, List[Dict[str, Any]]]]:
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

        # Filter out very short sentences and filler phrases
        filtered_segments = []
        filler_patterns = [
            r'^(yeah|yep|yes|no|okay|ok|um|uh|like|so|well|right|sure|exactly)\b',
            r'^\w{1,3}\b',  # Very short utterances
            r'^[^\w\s]+$',  # Only punctuation
        ]
        
        for i, seg in enumerate(content_segments):
            text = seg.get("text", "").strip().lower()
            
            # Skip if too short
            if len(text.split()) < 5:
                continue
                
            # Skip if matches filler patterns
            is_filler = any(re.match(pattern, text) for pattern in filler_patterns)
            if is_filler:
                continue
                
            filtered_segments.append((i, seg, sentences[i]))
        
        if not filtered_segments:
            logger.warning("All segments filtered out, using original segments")
            filtered_segments = [(i, seg, sentences[i]) for i, seg in enumerate(content_segments)]
        
        # Extract just the text for TF-IDF
        filtered_sentences = [item[2] for item in filtered_segments]

        # Use TF-IDF and cosine similarity to find important sentences
        vectorizer = TfidfVectorizer(
            stop_words='english',
            max_df=0.85,
            min_df=1,
            ngram_range=(1, 3),
            max_features=1000
        )
        try:
            # Create TF-IDF matrix
            tfidf_matrix = vectorizer.fit_transform(filtered_sentences)

            # Calculate similarity between sentences
            similarity_matrix = cosine_similarity(tfidf_matrix)

            # Calculate sentence scores based on centrality
            scores = np.sum(similarity_matrix, axis=1)
            
            # Also consider sentence length (prefer medium-length sentences)
            length_scores = np.array([min(len(s.split()), 30) / 30.0 for s in filtered_sentences])
            
            # Combine scores
            combined_scores = scores * 0.7 + length_scores * 0.3

            # Get indices of top sentences
            n_to_extract = min(n_sentences, len(filtered_segments))
            top_indices = np.argsort(combined_scores)[-n_to_extract:]

            # Sort indices by their position in the original text
            top_indices = sorted(top_indices)

            # Return the top segments with their metadata
            important_segments = [filtered_segments[i][1] for i in top_indices]
            return important_segments

        except Exception as e:
            logger.error(f"Error in extractive summarization: {e}")
            return content_segments[:n_sentences]

    def _generate_abstractive_summary(self, text: str, max_length: int = 150, min_length: int = 30) -> str:
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

            summary_text = summary[0]['summary_text']
            
            # Clean the summary
            cleaned_summary = self._clean_summary_text(summary_text)
            
            return cleaned_summary if cleaned_summary else summary_text

        except Exception as e:
            logger.error(f"Error in abstractive summarization: {e}")
            return f"Failed to generate abstractive summary: {str(e)}"

    def _generate_abstractive_summary_for_long_text(self, text: str, max_length: int = 150,
                                                    min_length: int = 30) -> str:
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
        logger.info(f"Identifying {num_topics} key topics")

        try:
            # Extended stop words list including common filler words
            custom_stop_words = set([
                'like', 'yeah', 'think', 'know', 'just', 'kind', 'sort', 'um', 'uh',
                'well', 'really', 'actually', 'basically', 'literally', 'okay', 'ok',
                'right', 'sure', 'probably', 'maybe', 'guess', 'thing', 'things',
                'stuff', 'lot', 'bit', 'little', 'going', 'gonna', 'want', 'need',
                'mean', 'got', 'get', 'say', 'said', 'tell', 'told', 'come', 'came',
                'make', 'made', 'way', 'time', 'good', 'bad', 'new', 'old', 'first',
                'last', 'long', 'great', 'little', 'own', 'other', 'old', 'right',
                'big', 'high', 'different', 'small', 'large', 'next', 'early', 'young',
                'important', 'public', 'bad', 'same', 'able', 'don', 'did', 'let',
                'level', 'look', 'looks', 'looked'
            ])
            
            # Clean the text first
            # Remove speaker labels
            text_cleaned = re.sub(r'Speaker_\d+:', '', text)
            
            # Split into words and filter
            words = re.findall(r'\b[a-zA-Z]{4,}\b', text_cleaned.lower())
            
            # Count word frequencies
            word_freq = Counter(words)
            
            # Remove stop words and custom stop words
            from sklearn.feature_extraction import _stop_words
            english_stops = _stop_words.ENGLISH_STOP_WORDS
            
            # Filter and get significant words
            significant_words = {}
            for word, count in word_freq.items():
                if (word not in custom_stop_words and 
                    word not in english_stops and
                    count >= 3 and  # Must appear at least 3 times
                    len(word) >= 4):  # At least 4 characters
                    significant_words[word] = count
            
            # Try extracting multi-word phrases (bigrams and trigrams)
            sentences = [s.strip() for s in re.split(r'[.!?]+', text_cleaned) if len(s.strip()) > 20]
            
            if len(sentences) >= 3:
                # Use TF-IDF for phrase extraction
                vectorizer = TfidfVectorizer(
                    max_df=0.6,
                    min_df=2,
                    stop_words='english',
                    max_features=100,
                    ngram_range=(2, 4),  # Bigrams to 4-grams
                    token_pattern=r'\b[a-zA-Z]{3,}\b'
                )
                
                try:
                    tfidf_matrix = vectorizer.fit_transform(sentences)
                    feature_names = vectorizer.get_feature_names_out()
                    scores = np.asarray(tfidf_matrix.sum(axis=0)).flatten()
                    
                    # Get top phrases
                    phrase_candidates = []
                    for idx in scores.argsort()[::-1]:
                        phrase = feature_names[idx]
                        
                        # Filter out phrases with stop words
                        phrase_words = phrase.split()
                        if any(word in custom_stop_words for word in phrase_words):
                            continue
                        
                        # Check if phrase is meaningful
                        if len(phrase) < 8 or len(phrase) > 50:
                            continue
                        
                        # Capitalize properly
                        capitalized = ' '.join(word.capitalize() for word in phrase_words)
                        phrase_candidates.append((capitalized, scores[idx]))
                        
                        if len(phrase_candidates) >= num_topics * 2:
                            break
                    
                    # If we found good phrases, use them
                    if phrase_candidates:
                        topics = [phrase for phrase, score in phrase_candidates[:num_topics]]
                        return topics
                        
                except Exception as e:
                    logger.warning(f"Phrase extraction failed: {e}, falling back to single words")
            
            # Fallback: use single significant words
            sorted_words = sorted(significant_words.items(), key=lambda x: x[1], reverse=True)
            topics = [word.capitalize() for word, count in sorted_words[:num_topics]]
            
            return topics if topics else ["No specific topics identified"]

        except Exception as e:
            logger.error(f"Error identifying topics: {e}")
            return ["Error identifying topics"]

    def _extract_action_items(self, transcript_segments: List[Dict[str, Any]]) -> List[str]:
        logger.info("Extracting action items")

        action_items = []
        
        # More specific action indicators
        action_patterns = [
            (r'\b(need to|needs to|needed to)\b', 'need'),
            (r'\b(should|ought to)\b', 'should'),
            (r'\b(will|\'ll)\b(?!.*\?)', 'will'),  # Exclude questions
            (r'\b(going to|gonna)\b', 'going to'),
            (r'\b(have to|has to|gotta)\b', 'must'),
            (r'\b(must|required to)\b', 'must'),
            (r'\b(let\'s|let us)\b', 'action'),
            (r'\b(task|action item|todo|to-do)\b', 'task'),
            (r'\b(follow[- ]up|follow up with)\b', 'follow-up'),
            (r'\b(schedule|arrange|organize|plan)\b', 'planning'),
            (r'\b(send|deliver|provide|share)\b', 'delivery'),
            (r'\b(review|check|verify|confirm)\b', 'review'),
            (r'\b(create|build|develop|implement)\b', 'development'),
        ]

        for segment in transcript_segments:
            text = segment.get("text", "").strip()
            text_lower = text.lower()
            speaker = segment.get("speaker", "")

            # Skip instructional or unknown speakers
            if speaker in ["Speaker_00", "Unknown"]:
                continue
                
            # Skip very short utterances
            if len(text.split()) < 5:
                continue

            # Check if the segment contains action indicators
            matched = False
            for pattern, category in action_patterns:
                if re.search(pattern, text_lower):
                    matched = True
                    break
            
            if not matched:
                continue
            
            # Additional filtering: skip questions and vague statements
            if text.strip().endswith('?'):
                continue
                
            # Skip if it's too vague or just contains filler
            filler_ratio = sum(1 for word in text_lower.split() 
                             if word in ['like', 'yeah', 'um', 'uh', 'just', 'really', 'kind', 'sort'])
            if filler_ratio > len(text.split()) * 0.3:  # More than 30% filler words
                continue
            
            # Clean up the text
            cleaned_text = re.sub(r'\s+', ' ', text).strip()
            
            # Limit length for readability
            if len(cleaned_text.split()) > 40:
                cleaned_text = ' '.join(cleaned_text.split()[:40]) + '...'
            
            # Add speaker information
            action_items.append(f"{speaker}: {cleaned_text}")

        # Remove duplicates while preserving order
        seen = set()
        unique_action_items = []
        for item in action_items:
            # Create a simplified version for duplicate checking
            simplified = re.sub(r'Speaker_\d+:', '', item).strip().lower()
            if simplified not in seen:
                seen.add(simplified)
                unique_action_items.append(item)

        return unique_action_items[:15]  # Limit to top 15 action items

    def summarize(
            self, transcript_data: Dict[str, Any],
            include_action_items: bool = True,
            max_summary_length: int = 150,
            min_summary_length: int = 30,
            num_extractive_sentences: int = 5
    ) -> Dict[str, Any]:
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
        logger.info(f"Saving markdown summary to {output_path}")

        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("# Meeting Summary\n\n")
                
                # Write metadata at the top
                metadata = summary_results['metadata']
                duration_min = metadata['duration'] / 60
                f.write(f"**Duration**: {duration_min:.1f} minutes | ")
                f.write(f"**Participants**: {metadata['num_speakers']} | ")
                f.write(f"**Language**: {metadata['language']}\n\n")
                f.write("---\n\n")

                # Write abstractive summary (main overview)
                f.write("## Overview\n\n")
                abstractive = summary_results["summary"]["abstractive"]
                if abstractive and len(abstractive.strip()) > 10:
                    f.write(abstractive)
                else:
                    # Fallback: create overview from key quotes if abstractive failed
                    f.write("This meeting covered the following key points:\n\n")
                    for i, quote in enumerate(summary_results["summary"]["extractive"][:3], 1):
                        f.write(f"{i}. {quote}\n")
                f.write("\n\n")

                # Write key topics with better formatting
                key_topics = summary_results["summary"]["key_topics"]
                if key_topics:
                    f.write("## Key Topics Discussed\n\n")
                    for i, topic in enumerate(key_topics, 1):
                        f.write(f"{i}. **{topic}**\n")
                    f.write("\n")

                # Write key quotes (extractive) with better formatting
                extractive = summary_results["summary"]["extractive"]
                if extractive:
                    f.write("## Important Discussion Points\n\n")
                    for i, quote in enumerate(extractive, 1):
                        # Clean the quote
                        cleaned_quote = quote.strip()
                        f.write(f"{i}. *\"{cleaned_quote}\"*\n\n")

                # Write action items if any
                action_items = summary_results["summary"]["action_items"]
                if action_items:
                    f.write("## Action Items\n\n")
                    for item in action_items:
                        f.write(f"- [ ] {item}\n")
                    f.write("\n")
                else:
                    f.write("## Action Items\n\n")
                    f.write("*No specific action items identified in this meeting.*\n\n")

                # Write speaker statistics
                f.write("## Speaker Statistics\n\n")
                f.write("| Speaker | Speaking Time | Utterances | Total Words | Avg Words/Utterance |\n")
                f.write("|---------|---------------|------------|-------------|---------------------|\n")
                
                # Sort speakers by speaking time
                sorted_speakers = sorted(
                    summary_results["speaker_stats"].items(),
                    key=lambda x: x[1]['speaking_time'],
                    reverse=True
                )
                
                for speaker, stats in sorted_speakers:
                    time_min = stats['speaking_time'] / 60
                    f.write(f"| {speaker} | {time_min:.1f} min | {stats['utterances']} | {stats['total_words']} | {stats['avg_words_per_utterance']:.1f} |\n")

                f.write("\n---\n")
                f.write(f"\n*Summary generated on {metadata.get('original_metadata', {}).get('timestamp', 'N/A')}*\n")

            logger.info(f"Markdown summary saved successfully to {output_path}")

        except Exception as e:
            logger.error(f"Error saving markdown summary: {e}")