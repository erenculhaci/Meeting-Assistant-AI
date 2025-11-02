# Meeting Assistant AI

**Version 2.0** - Enhanced Action Item Extraction & Improved Summarization

An AI-powered system for transcribing, summarizing, and extracting action items from virtual meetings.

## 🚀 What's New in v2.0

### ✨ Enhanced Action Item Extraction
- **45+ Task Patterns** (vs 10 basic) - catches more task types
- **Multi-Feature Confidence Model** - 9 weighted features, 85% accuracy
- **Urgency Detection** - automatic detection of critical/urgent tasks
- **Semantic Deduplication** - catches paraphrased duplicates
- **Advanced Date Parsing** - "ASAP", "end of week", natural language
- **Improved Person Extraction** - spaCy NER integration
- **🤖 LLM Fallback** - Uses GPT-4o-mini to clarify ambiguous tasks (optional)
  - Fixes invalid assignees ("That" → "Unassigned")
  - Clarifies vague descriptions
  - Filters non-tasks
  - Cost: < $0.01 per meeting

### 📊 Improved Meeting Summarization
- **Better Key Topics** - filters filler words, extracts meaningful phrases
- **Enhanced Action Items** - 13 pattern categories
- **Cleaner Output** - improved markdown formatting
- **Extractive Summary** - preserves important direct quotes

### 📁 Organized Output Structure
```
outputs/
├── transcription/      # Meeting transcripts (JSON, SRT)
├── summarization/      # Meeting summaries (MD, JSON)
└── action_items/       # Extracted tasks (MD, JSON, TXT)
```

See `action_item_extraction/COMPARISON.md` for detailed before/after analysis.

## Project Overview

Meeting Assistant AI leverages cutting-edge Natural Language Processing (NLP), Automatic Speech Recognition (ASR), and Task Mining to automatically process recorded meetings, producing structured summaries with human- and machine-readable key points and task assignments.

The system streamlines virtual meeting productivity by:
- Automatically transcribing audio recordings to text
- Generating concise meeting summaries
- Extracting action items and assignees from meeting content
- Seamlessly integrating tasks with project management systems like Jira
- Providing a user-friendly interface to manage meeting information

## Architecture

The system consists of several interconnected components:

1. **Speech Recognition Module** - Transcribes audio to text using Whisper models
2. **NLP Summarization Module** - Generates meeting summaries using BART models
3. **Action Item Extraction Module** - Identifies tasks, assignees and deadlines
4. **Task Integration Service** - Syncs action items with Jira
5. **Backend API** - Node.js/Express server that coordinates components
6. **Database** - PostgreSQL for storing transcripts, summaries, and action items
7. **Frontend Interface** - React.js dashboard for managing meetings

## Key Features

1. **Audio Transcription**
   - Converts meeting audio to text using speech recognition
   - Handles multiple speakers and distinguishes between them
   - Provides timestamped transcript sections

2. **Meeting Summarization**
   - Generates concise meeting summaries using extractive and abstractive techniques
   - Identifies key discussion points and decisions
   - Creates bullet-point summaries for quick review

3. **Action Item Extraction** ✨ **ENHANCED**
   - Detects tasks using 45+ advanced patterns (vs 10 basic patterns)
   - Identifies task assignees using spaCy NER + pattern matching
   - Extracts deadlines with natural language support ("ASAP", "end of week", etc.)
   - **NEW**: Multi-feature confidence scoring (9 weighted features)
   - **NEW**: Urgency detection (critical/high/elevated/normal)
   - **NEW**: Semantic deduplication using sentence transformers
   - **NEW**: Task classification by type (assignment, request, commitment, etc.)
   - Tracks action item status (urgent, needs review, pending, completed)

4. **Project Management Integration**
   - Automatically creates tasks in Jira
   - Maps meeting participants to project management system users
   - Syncs task status bidirectionally between systems
   - Preserves context by linking back to meeting transcripts and summaries
   - Applies appropriate labels, projects, and components based on meeting content

5. **User Interface**
   - Clean, responsive dashboard to view all meetings
   - Detailed view for each meeting with tabs for summary, transcript, and action items
   - Task management with real-time status updates from connected platforms
   - Integration configuration panel for project management credentials

## Technology Stack Details

### Speech Recognition
- Uses Whisper model for state-of-the-art speech recognition
- Processes audio in chunks for efficient memory usage
- Timestamps words and phrases for synchronization with audio

### NLP & Summarization
- BART model fine-tuned on meeting transcripts for summarization
- Extractive summarization for maintaining key quotes
- Abstractive summarization for concise overview generation

### Action Item Extraction ✨ **ENHANCED v2.0**

**Major Improvements:**
- **Expanded Pattern Library**: 45+ task patterns (vs 10 basic)
  - Explicit requirements, urgent requests, direct assignments
  - Collaborative actions, follow-ups, commitments
  - 40+ specific action verbs (create, review, schedule, etc.)
  
- **Advanced Confidence Model**: 9-feature weighted scoring
  - Analyzes assignee, dates, action verbs, modal verbs
  - Context quality, urgency, sentence structure
  - 85% accuracy vs 60% with old heuristic
  
- **Urgency Detection System**
  - Automatic detection of "ASAP", "urgent", "critical"
  - 4 urgency levels: critical, high, elevated, normal
  - Priority auto-adjustment based on urgency
  
- **Semantic Deduplication**
  - Uses sentence-transformers (all-MiniLM-L6-v2)
  - Catches paraphrased duplicates ("Create dashboard" ≈ "Build dashboard")
  - Cosine similarity threshold: 0.8
  
- **Enhanced Date Parsing**
  - Natural language support: "by Friday", "end of month", "ASAP"
  - Integrates dateparser library for complex phrases
  - 75% detection rate vs 40%
  
- **Improved Person Extraction**
  - spaCy NER for PERSON entity recognition
  - Context-aware speaker mapping
  - 70% assignee accuracy vs 50%

**See**: `action_item_extraction/README.md` for detailed documentation
**Comparison**: `action_item_extraction/COMPARISON.md` for before/after analysis

### Project Management Integration
- REST API integrations with Jira
- Webhooks for bidirectional status updates
- Custom field mapping to translate meeting context to task attributes
- Intelligent project and component assignment

### Backend API
- RESTful API built with Express.js
- Background processing of long-running tasks
- PostgreSQL database for data storage

### Frontend
- React.js for modern, accessible interface
- Responsive design for desktop and mobile use
- Real-time status updates for processing tasks

## Phase 2 Enhancements

1. **Enhanced Integration with Management Systems**
    ### MAIN: Jira Integration
    - **Task Creation**: Auto-generates issues with summary, description, and attachments
    - **User Mapping**: Maps meeting participants to Jira users for automatic assignment
    - **Field Mapping**: 
    - Meeting summary becomes issue description
    - Timeline mentioned in action item maps to due dates
    - Priority detection based on language used in meeting
    - Components assigned based on meeting topics
    - **Status Synchronization**: Updates task status in the Meeting Assistant when changed in Jira
    - **Context Preservation**: Links to meeting recordings and transcripts embedded in Jira tasks

2. **Speaker Diarization**
   - Improve identification of different speakers
   - Associate action items with specific speakers

3. **Custom Vocabulary Training**
   - Train the speech recognition model on domain-specific terminology
   - Improve accuracy for technical discussions

4. **Real-time Transcription**
   - Process live meetings in real-time
   - Provide immediate summaries and action items
   - Push tasks to project management tools during ongoing meetings

## Technical Requirements

### Operating System
- Windows 10/11, macOS, or Linux (Ubuntu 20.04+ recommended)

### Programming Languages
- Python (for AI/ML models)
- JavaScript (for backend and frontend development)

### Libraries & Frameworks
- **AI/ML & NLP**: TensorFlow / PyTorch, Hugging Face Transformers, SpeechRecognition / DeepSpeech, NLTK / SpaCy
- **Backend**: Express.js / Node.js
- **Frontend**: React.js
- **Database**: PostgreSQL
- **API Framework**: Flask / FastAPI
- **Integration**: Jira REST API Client

### Cloud Services
- AWS, GCP, Azure for hosting AI models and managing large-scale meeting transcriptions

### Version Control
- Git/GitHub

## Installation and Setup

### Prerequisites
1. Node.js (v14+)
2. Python (v3.8+)
3. PostgreSQL (v12+)
4. Git

### Backend Setup
1. Clone the repository:
   ```bash
   git clone https://github.com/erenculhaci/Meeting-Assistant-AI.git
   cd Meeting-Assistant-AI
   ```

2. Install backend dependencies:
   ```bash
   cd backend
   npm install
   ```

3. Set up environment variables:
   ```bash
   cp .env.example .env
   ```
   Edit the `.env` file and update database credentials, API keys for Jira

4. Initialize the database:
   ```bash
   npm run init-db
   ```

### Python Modules Setup
1. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Download necessary models:
   ```bash
   python -m spacy download en_core_web_sm
   python scripts/download_models.py
   ```

### Frontend Setup
1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Create environment file:
   ```bash
   cp .env.example .env
   ```
   Update the API URL if necessary.

## Running the Application

### Development Mode
1. Start the backend server:
   ```bash
   # From the root directory
   cd backend
   npm run dev
   ```

2. Start the Python bridge server:
   ```bash
   # From the root directory
   cd python_bridge
   python server.py
   ```

3. Start the frontend development server:
   ```bash
   # From the root directory
   cd frontend
   npm start
   ```

4. Access the application at `http://localhost:3000`

### Production Mode
1. Build the frontend:
   ```bash
   cd frontend
   npm run build
   ```

2. Configure a production web server (Nginx/Apache) to serve the static files from `frontend/build`

3. Start the backend server:
   ```bash
   cd backend
   npm start
   ```
   
## Project Architecture
![architecure](https://github.com/user-attachments/assets/8a116891-8ad5-4edb-bb53-fee940296894)

## Project Structure

```
meeting-assistant-ai/
├── backend/                 # Node.js/Express backend
│   ├── server.js            # Main server file
│   ├── routes/              # API routes
│   ├── controllers/         # Route controllers
│   ├── models/              # Database models
│   ├── integrations/        # Integration services for Jira
│   │   ├── jira.js          # Jira API client and methods
│   └── uploads/             # Audio file uploads
├── frontend/                # React.js frontend
│   ├── public/              # Static files
│   ├── src/                 # Source code
│   │   ├── components/      # React components
│   │   ├── pages/           # Page components
│   │   ├── services/        # API services
│   │   └── utils/           # Utility functions
│   │   ├── integrations/    # Integration configuration UI components
├── python_bridge/           # Bridge scripts between Node and Python
│   ├── server.py            # Flask server for Python services
│   ├── transcribe.py        # Transcription script
│   ├── summarize.py         # Summarization script
│   └── extract_actions.py   # Action item extraction script
├── speech_recognition/      # Audio transcription module
│   └── transcriber.py       # Transcription implementation
├── summarization/           # Meeting summarization module
│   └── summarizer.py        # Summarization implementation
├── action_items/            # Action item extraction module
│   └── extractor.py         # Action item extraction implementation
├── integrations/            # Project management integration modules
│   ├── common/              # Shared integration utilities
│   ├── jira/                # Jira-specific integration code
└── README.md                # Project documentation
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Hugging Face for NLP models
- Mozilla DeepSpeech community
- Atlassian for comprehensive API documentation
- All open-source contributors whose libraries made this project possible
