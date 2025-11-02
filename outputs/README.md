# Output Organization

All outputs from the Meeting Assistant AI are now organized into dedicated subdirectories within the `outputs/` folder for better structure and clarity.

## Directory Structure

```
outputs/
├── transcription/          # Speech-to-text outputs
│   ├── transcript.json
│   ├── transcript2.json
│   ├── meeting_transcript.json
│   ├── meeting_transcript.srt
│   └── meeting_transcript2.json
│
├── summarization/          # Meeting summary outputs
│   ├── meeting_summary.json
│   ├── meeting_summary.md
│   ├── meeting_summary_cli.md
│   └── meeting_summary_improved.md
│
└── action_items/           # Extracted action items & tasks
    ├── action_items.json
    ├── action_items.md
    └── action_items_cli.json
```

## Output Types

### 📝 Transcription (`outputs/transcription/`)

Contains all speech recognition and transcription outputs:

- **JSON format** (`.json`): Complete transcription with speaker diarization, timestamps, and metadata
- **SRT format** (`.srt`): Subtitle file format with timestamps (useful for video subtitles)

**Default output path**: When using the transcription module without specifying an output file, files will be saved to `outputs/transcription/`

### 📊 Summarization (`outputs/summarization/`)

Contains all meeting summary outputs:

- **JSON format** (`.json`): Structured summary with metadata, topics, and statistics
- **Markdown format** (`.md`): Human-readable summary with formatted sections
- **Text format** (`.txt`): Plain text summary

**Default output path**: `outputs/summarization/`

### ✅ Action Items (`outputs/action_items/`)

Contains extracted tasks and action items:

- **JSON format** (`.json`): Structured task data with assignees, deadlines, and priorities
- **Markdown format** (`.md`): Formatted task list with checkboxes and details
- **Text format** (`.txt`): Plain text task list

**Default output path**: `outputs/action_items/`

## Usage Examples

### Transcription

```python
from speech_recognition.transcriber import transcribe_meeting

result = transcribe_meeting(
    "audio/meeting.wav",
    output_format="json",
    output_file="outputs/transcription/my_meeting.json"
)
```

### Summarization

```python
from summarization.summarizer import summarize_meeting

summary = summarize_meeting(
    "outputs/transcription/my_meeting.json",
    output_format="md",
    output_file="outputs/summarization/my_meeting_summary.md"
)
```

### Action Item Extraction

```python
from action_item_extraction.extractor import extract_action_items

tasks = extract_action_items(
    "outputs/transcription/my_meeting.json",
    output_format="md",
    output_file="outputs/action_items/my_meeting_tasks.md"
)
```

## CLI Usage

All CLI tools now use the organized structure by default:

```bash
# Summarization (outputs to outputs/summarization/)
python -m summarization.cli transcript.json

# Action items (outputs to outputs/action_items/)
python -m action_item_extraction.cli transcript.json

# Custom output directory
python -m summarization.cli transcript.json --output_dir custom/path/
```

## Benefits

✅ **Better Organization**: Easy to find outputs by type  
✅ **Cleaner Structure**: No mixed files in root outputs folder  
✅ **Pipeline Friendly**: Natural flow from transcription → summarization → action items  
✅ **Version Control**: Easier to gitignore specific output types  
✅ **Scalability**: Can handle multiple meeting outputs without clutter

## Migration

If you have existing code that references old paths (e.g., `outputs/transcript.json`), update them to:

- `outputs/transcript.json` → `outputs/transcription/transcript.json`
- `outputs/meeting_summary.md` → `outputs/summarization/meeting_summary.md`
- `outputs/action_items.json` → `outputs/action_items/action_items.json`
