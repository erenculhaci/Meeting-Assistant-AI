
# Meeting Assistant AI
A complete AI-powered system for transcribing, summarizing, and extracting action items from meetings, with seamless Jira integration and modern web interface.

![system_arch](https://github.com/user-attachments/assets/e2cb3a7e-58e6-4b5c-9719-7126bc5dcab4)<img width="2501" height="1263" alt="image" src="https://github.com/user-attachments/assets/7cce6a39-475e-4725-b631-8d94eaa8659d" />

## 🎯 Overview

Meeting Assistant AI streamlines meeting productivity by automatically:
- **Transcribing** audio/video recordings with speaker diarization
- **Generating** concise meeting summaries with key topics
- **Extracting** action items with assignees and deadlines
- **Creating** Jira issues directly from tasks
- **Managing** meetings through a modern web interface


### 🌐 Full-Stack Web Application
- **Modern UI**: React 19 + TypeScript + Tailwind CSS 4
- **FastAPI Backend**: Async Python with PostgreSQL
- **Multi-User Support**: JWT + Google OAuth authentication
- **Real-time Progress**: Live status tracking with localStorage persistence
- **Responsive Design**: Works seamlessly on desktop, tablet, and mobile

### ✨ Enhanced Action Item Extraction
- **45+ Task Patterns** (vs 10 basic) - catches more task types
- **Multi-Feature Confidence Model** - 9 weighted features, 85% accuracy
- **Urgency Detection** - automatic detection of critical/urgent tasks
- **Semantic Deduplication** - catches paraphrased duplicates using sentence transformers
- **Advanced Date Parsing** - "ASAP", "next Friday", "end of week", natural language
- **Improved Person Extraction** - spaCy NER integration
- **🤖 LLM Fallback** - Uses Groq LLaMA to clarify ambiguous tasks (optional)

### 📊 Improved Meeting Summarization
- **Better Key Topics** - filters filler words, extracts meaningful phrases
- **Enhanced Action Items** - 13 pattern categories with context
- **Cleaner Output** - improved markdown formatting
- **Extractive Summary** - preserves important direct quotes

### 🔗 Advanced Jira Integration
- **Smart Assignee Matching** - Fuzzy name matching with Jira users
- **Multi-Assignee Support** - Automatically splits tasks for multiple people
- **Intelligent Date Parsing** - Converts vague dates ("Saturday night") to yyyy-MM-dd
- **Bulk Issue Creation** - Create multiple issues at once
- **User Mappings** - Manual mappings for ambiguous names

### 📁 Organized Output Structure
```
outputs/
├── transcription/      # Meeting transcripts (JSON, SRT)
├── summarization/      # Meeting summaries (MD, JSON)
└── action_items/       # Extracted tasks (MD, JSON, TXT)
```

## 🏗 Architecture

![Uploading <svg viewBox="0 0 1200 800" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <!-- Gradients -->
    <linearGradient id="clientGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" style="stop-color:#06b6d4;stop-opacity:0.2" />
      <stop offset="100%" style="stop-color:#3b82f6;stop-opacity:0.2" />
    </linearGradient>
    <linearGradient id="appGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" style="stop-color:#a855f7;stop-opacity:0.2" />
      <stop offset="100%" style="stop-color:#ec4899;stop-opacity:0.2" />
    </linearGradient>
    <linearGradient id="aiGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" style="stop-color:#10b981;stop-opacity:0.2" />
      <stop offset="100%" style="stop-color:#14b8a6;stop-opacity:0.2" />
    </linearGradient>
    <linearGradient id="dataGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" style="stop-color:#f97316;stop-opacity:0.2" />
      <stop offset="100%" style="stop-color:#ef4444;stop-opacity:0.2" />
    </linearGradient>
    
    <!-- Arrow marker -->
    <marker id="arrowhead" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto">
      <polygon points="0 0, 10 3, 0 6" fill="#a855f7" />
    </marker>
  </defs>
  
  <!-- Background -->
  <rect width="1200" height="800" fill="#0f172a"/>
  
  <!-- Title -->
  <text x="600" y="40" font-family="Arial, sans-serif" font-size="32" font-weight="bold" fill="#ffffff" text-anchor="middle">
    Meeting Assistant AI - System Architecture
  </text>
  
  <!-- CLIENT LAYER -->
  <rect x="50" y="80" width="1100" height="120" rx="12" fill="url(#clientGrad)" stroke="#06b6d4" stroke-width="2"/>
  <text x="70" y="110" font-family="Arial, sans-serif" font-size="18" font-weight="bold" fill="#06b6d4">CLIENT LAYER</text>
  
  <rect x="80" y="125" width="310" height="60" rx="8" fill="#0f172a" stroke="#06b6d4" stroke-width="1.5"/>
  <text x="235" y="150" font-family="Arial, sans-serif" font-size="14" font-weight="bold" fill="#ffffff" text-anchor="middle">React 19 Frontend</text>
  <text x="235" y="168" font-family="Arial, sans-serif" font-size="11" fill="#94a3b8" text-anchor="middle">TypeScript • Vite • Tailwind CSS 4</text>
  <text x="235" y="182" font-family="Arial, sans-serif" font-size="11" fill="#94a3b8" text-anchor="middle">React Router • Axios</text>
  
  <rect x="420" y="125" width="310" height="60" rx="8" fill="#0f172a" stroke="#06b6d4" stroke-width="1.5"/>
  <text x="575" y="150" font-family="Arial, sans-serif" font-size="14" font-weight="bold" fill="#ffffff" text-anchor="middle">Authentication</text>
  <text x="575" y="168" font-family="Arial, sans-serif" font-size="11" fill="#94a3b8" text-anchor="middle">JWT • Google OAuth 2.0</text>
  <text x="575" y="182" font-family="Arial, sans-serif" font-size="11" fill="#94a3b8" text-anchor="middle">Token Management</text>
  
  <rect x="760" y="125" width="310" height="60" rx="8" fill="#0f172a" stroke="#06b6d4" stroke-width="1.5"/>
  <text x="915" y="150" font-family="Arial, sans-serif" font-size="14" font-weight="bold" fill="#ffffff" text-anchor="middle">UI Components</text>
  <text x="915" y="168" font-family="Arial, sans-serif" font-size="11" fill="#94a3b8" text-anchor="middle">Meeting Upload • Results View</text>
  <text x="915" y="182" font-family="Arial, sans-serif" font-size="11" fill="#94a3b8" text-anchor="middle">Jira Configuration</text>
  
  <!-- Arrow 1 -->
  <line x1="600" y1="210" x2="600" y2="240" stroke="#a855f7" stroke-width="3" marker-end="url(#arrowhead)"/>
  <text x="640" y="228" font-family="Arial, sans-serif" font-size="12" fill="#a855f7" font-weight="bold">REST API</text>
  
  <!-- APPLICATION LAYER -->
  <rect x="50" y="250" width="1100" height="120" rx="12" fill="url(#appGrad)" stroke="#a855f7" stroke-width="2"/>
  <text x="70" y="280" font-family="Arial, sans-serif" font-size="18" font-weight="bold" fill="#a855f7">APPLICATION LAYER</text>
  
  <rect x="80" y="295" width="250" height="60" rx="8" fill="#0f172a" stroke="#a855f7" stroke-width="1.5"/>
  <text x="205" y="320" font-family="Arial, sans-serif" font-size="14" font-weight="bold" fill="#ffffff" text-anchor="middle">FastAPI Backend</text>
  <text x="205" y="338" font-family="Arial, sans-serif" font-size="11" fill="#94a3b8" text-anchor="middle">SQLAlchemy 2.0 • Async</text>
  <text x="205" y="352" font-family="Arial, sans-serif" font-size="11" fill="#94a3b8" text-anchor="middle">Uvicorn ASGI</text>
  
  <rect x="360" y="295" width="250" height="60" rx="8" fill="#0f172a" stroke="#a855f7" stroke-width="1.5"/>
  <text x="485" y="320" font-family="Arial, sans-serif" font-size="14" font-weight="bold" fill="#ffffff" text-anchor="middle">API Routes</text>
  <text x="485" y="338" font-family="Arial, sans-serif" font-size="11" fill="#94a3b8" text-anchor="middle">Auth • Meetings • Jira</text>
  <text x="485" y="352" font-family="Arial, sans-serif" font-size="11" fill="#94a3b8" text-anchor="middle">Assignees • CRUD</text>
  
  <rect x="640" y="295" width="250" height="60" rx="8" fill="#0f172a" stroke="#a855f7" stroke-width="1.5"/>
  <text x="765" y="320" font-family="Arial, sans-serif" font-size="14" font-weight="bold" fill="#ffffff" text-anchor="middle">Services Layer</text>
  <text x="765" y="338" font-family="Arial, sans-serif" font-size="11" fill="#94a3b8" text-anchor="middle">Meeting Processor</text>
  <text x="765" y="352" font-family="Arial, sans-serif" font-size="11" fill="#94a3b8" text-anchor="middle">Background Jobs</text>
  
  <rect x="920" y="295" width="230" height="60" rx="8" fill="#0f172a" stroke="#a855f7" stroke-width="1.5"/>
  <text x="1035" y="320" font-family="Arial, sans-serif" font-size="14" font-weight="bold" fill="#ffffff" text-anchor="middle">Security</text>
  <text x="1035" y="338" font-family="Arial, sans-serif" font-size="11" fill="#94a3b8" text-anchor="middle">JWT • bcrypt</text>
  <text x="1035" y="352" font-family="Arial, sans-serif" font-size="11" fill="#94a3b8" text-anchor="middle">CORS Protection</text>
  
  <!-- Arrow 2 -->
  <line x1="600" y1="380" x2="600" y2="410" stroke="#10b981" stroke-width="3" marker-end="url(#arrowhead)"/>
  <text x="640" y="398" font-family="Arial, sans-serif" font-size="12" fill="#10b981" font-weight="bold">Processing Pipeline</text>
  
  <!-- AI PROCESSING LAYER -->
  <rect x="50" y="420" width="1100" height="150" rx="12" fill="url(#aiGrad)" stroke="#10b981" stroke-width="2"/>
  <text x="70" y="450" font-family="Arial, sans-serif" font-size="18" font-weight="bold" fill="#10b981">AI PROCESSING LAYER</text>
  
  <rect x="80" y="465" width="330" height="90" rx="8" fill="#0f172a" stroke="#10b981" stroke-width="1.5"/>
  <text x="245" y="488" font-family="Arial, sans-serif" font-size="14" font-weight="bold" fill="#ffffff" text-anchor="middle">🎤 Speech Recognition</text>
  <text x="245" y="506" font-family="Arial, sans-serif" font-size="11" fill="#94a3b8" text-anchor="middle">① Whisper Model</text>
  <text x="245" y="520" font-family="Arial, sans-serif" font-size="11" fill="#94a3b8" text-anchor="middle">② Speaker Diarization (Pyannote)</text>
  <text x="245" y="534" font-family="Arial, sans-serif" font-size="11" fill="#94a3b8" text-anchor="middle">③ SRT Generation</text>
  <text x="245" y="550" font-family="Arial, sans-serif" font-size="10" fill="#10b981" text-anchor="middle" font-weight="bold">→ Transcripts (JSON, SRT)</text>
  
  <rect x="435" y="465" width="330" height="90" rx="8" fill="#0f172a" stroke="#10b981" stroke-width="1.5"/>
  <text x="600" y="488" font-family="Arial, sans-serif" font-size="14" font-weight="bold" fill="#ffffff" text-anchor="middle">🧠 Summarization</text>
  <text x="600" y="506" font-family="Arial, sans-serif" font-size="11" fill="#94a3b8" text-anchor="middle">① Groq LLaMA 3.3</text>
  <text x="600" y="520" font-family="Arial, sans-serif" font-size="11" fill="#94a3b8" text-anchor="middle">② Key Topics Extraction</text>
  <text x="600" y="534" font-family="Arial, sans-serif" font-size="11" fill="#94a3b8" text-anchor="middle">③ Action Items Identification</text>
  <text x="600" y="550" font-family="Arial, sans-serif" font-size="10" fill="#10b981" text-anchor="middle" font-weight="bold">→ Summaries (MD, JSON)</text>
  
  <rect x="790" y="465" width="330" height="90" rx="8" fill="#0f172a" stroke="#10b981" stroke-width="1.5"/>
  <text x="955" y="488" font-family="Arial, sans-serif" font-size="14" font-weight="bold" fill="#ffffff" text-anchor="middle">⚙️ Task Extraction</text>
  <text x="955" y="506" font-family="Arial, sans-serif" font-size="11" fill="#94a3b8" text-anchor="middle">① 45+ Task Patterns</text>
  <text x="955" y="520" font-family="Arial, sans-serif" font-size="11" fill="#94a3b8" text-anchor="middle">② NER (spaCy) + Confidence Scoring</text>
  <text x="955" y="534" font-family="Arial, sans-serif" font-size="11" fill="#94a3b8" text-anchor="middle">③ Semantic Deduplication</text>
  <text x="955" y="550" font-family="Arial, sans-serif" font-size="10" fill="#10b981" text-anchor="middle" font-weight="bold">→ Tasks (MD, JSON, TXT)</text>
  
  <!-- Arrow 3 -->
  <line x1="600" y1="580" x2="600" y2="610" stroke="#f97316" stroke-width="3" marker-end="url(#arrowhead)"/>
  <text x="640" y="598" font-family="Arial, sans-serif" font-size="12" fill="#f97316" font-weight="bold">Data Persistence</text>
  
  <!-- DATA & INTEGRATION LAYER -->
  <rect x="50" y="620" width="1100" height="120" rx="12" fill="url(#dataGrad)" stroke="#f97316" stroke-width="2"/>
  <text x="70" y="650" font-family="Arial, sans-serif" font-size="18" font-weight="bold" fill="#f97316">DATA &amp; INTEGRATION LAYER</text>
  
  <rect x="80" y="665" width="330" height="60" rx="8" fill="#0f172a" stroke="#f97316" stroke-width="1.5"/>
  <text x="245" y="690" font-family="Arial, sans-serif" font-size="14" font-weight="bold" fill="#ffffff" text-anchor="middle">🐘 PostgreSQL Database</text>
  <text x="245" y="708" font-family="Arial, sans-serif" font-size="11" fill="#94a3b8" text-anchor="middle">Users • Meetings • Action Items</text>
  <text x="245" y="722" font-family="Arial, sans-serif" font-size="11" fill="#94a3b8" text-anchor="middle">Jira Config • Auth Tokens</text>
  
  <rect x="435" y="665" width="330" height="60" rx="8" fill="#0f172a" stroke="#f97316" stroke-width="1.5"/>
  <text x="600" y="690" font-family="Arial, sans-serif" font-size="14" font-weight="bold" fill="#ffffff" text-anchor="middle">📁 File Storage</text>
  <text x="600" y="708" font-family="Arial, sans-serif" font-size="11" fill="#94a3b8" text-anchor="middle">Audio/Video Files • Transcripts</text>
  <text x="600" y="722" font-family="Arial, sans-serif" font-size="11" fill="#94a3b8" text-anchor="middle">Summaries • Output Files</text>
  
  <rect x="790" y="665" width="330" height="60" rx="8" fill="#0f172a" stroke="#f97316" stroke-width="1.5"/>
  <text x="955" y="690" font-family="Arial, sans-serif" font-size="14" font-weight="bold" fill="#ffffff" text-anchor="middle">☁️ External APIs</text>
  <text x="955" y="708" font-family="Arial, sans-serif" font-size="11" fill="#94a3b8" text-anchor="middle">Jira REST API • Groq AI</text>
  <text x="955" y="722" font-family="Arial, sans-serif" font-size="11" fill="#94a3b8" text-anchor="middle">Google OAuth</text>
  
  <!-- Footer -->
  <text x="600" y="770" font-family="Arial, sans-serif" font-size="12" fill="#94a3b8" text-anchor="middle">
    🐍 Python 3.11+ • ⚡ Node.js 18+ • 🐘 PostgreSQL 12+ • 🐳 Docker Ready
  </text>
  <text x="600" y="790" font-family="Arial, sans-serif" font-size="11" fill="#64748b" text-anchor="middle">
    Made with ❤️ by Eren Culhaci | MIT License
  </text>
</svg>system_arch.svg…]()

### Components

1. **Web Application** (`webapp/`)
   - **Frontend**: React + TypeScript SPA with Vite
   - **Backend**: FastAPI async server with PostgreSQL
   - **Authentication**: JWT + Google OAuth
   - **File Storage**: Local uploads with background processing

2. **Speech Recognition** (`speech_recognition/`)
   - Whisper model for transcription
   - Speaker diarization with Pyannote
   - SRT subtitle generation

3. **Summarization** (`summarization/`)
   - Groq LLaMA for meeting summaries
   - Key topic extraction
   - Action item identification

4. **Action Item Extraction** (`action_item_extraction/`)
   - 45+ task patterns with confidence scoring
   - Named entity recognition for assignees
   - Natural language date parsing
   - Semantic deduplication

5. **Jira Integration**
   - REST API client for issue creation
   - User mapping and auto-assignment
   - Bidirectional sync capabilities

## 🛠 Technology Stack

### Frontend
- **React 19** with React Compiler
- **TypeScript** for type safety
- **Vite** for fast builds
- **Tailwind CSS 4** for styling
- **React Router 6** for navigation
- **Axios** for API calls

### Backend
- **FastAPI** - Modern async Python framework
- **PostgreSQL** - Relational database
- **SQLAlchemy 2.0** - Async ORM
- **JWT** - Authentication
- **httpx** - Async HTTP client

### AI/ML
- **Whisper** - Speech-to-text
- **Groq LLaMA 3.3** - Text summarization and extraction
- **spaCy** - Named entity recognition
- **Sentence Transformers** - Semantic similarity
- **Pyannote** - Speaker diarization

### Infrastructure
- **PostgreSQL 12+** - Database
- **Python 3.11+** - Backend runtime
- **Node.js 18+** - Frontend build
- **Uvicorn** - ASGI server

## 📦 Installation

### Prerequisites
```bash
# Required
Python 3.11+
Node.js 18+
PostgreSQL 12+

# Get free API key
Groq API Key: https://console.groq.com/keys
```

### 1. Clone Repository
```bash
git clone https://github.com/erenculhaci/Meeting-Assistant-AI.git
cd Meeting-Assistant-AI
```

### 3. Environment Configuration

Create `.env` file in the project root:

```env
# Groq API Key (FREE - get from https://console.groq.com/keys)
GROQ_API_KEY=gsk_your_api_key_here

# Database Configuration
DATABASE_URL=postgresql+asyncpg://postgres:your_password@localhost:5432/meeting_assistant

# JWT Authentication
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Google OAuth (optional)
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=http://localhost:8000/api/auth/google/callback
FRONTEND_URL=http://localhost:5173

# Application Settings
DEBUG=false
ENVIRONMENT=production
WHISPER_MODEL=base
```

### 4. Backend Setup
```bash
cd webapp/backend

# Create virtual environment
python -m venv ../../venv
source ../../venv/bin/activate  # Windows: ..\..\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start server
uvicorn main:app --reload --port 8000
```

### 5. Frontend Setup
```bash
cd webapp/frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### 6. Access Application
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## 🎯 Usage

### Quick Start
1. **Sign Up**: Create account with email/password or Google
2. **Upload Meeting**: Drag & drop audio/video file (MP3, MP4, WAV, etc.)
3. **Wait for Processing**: Watch real-time progress (transcription → summarization → extraction)
4. **Review Results**: View summary, transcript, and extracted tasks
5. **Configure Jira** (optional): Add credentials in Jira Settings
6. **Create Issues**: Select tasks and push to Jira with one click

### Advanced Features

#### Multi-Assignee Support
```
Task: "Eren and Azra should review the dashboard"
→ Creates 2 separate Jira issues (one for Eren, one for Azra)
```

#### Intelligent Date Parsing
```
"Saturday night"     → Next Saturday (2025-12-20)
"next Monday"        → Monday of next week (2025-12-22)
"end of week"        → Next Friday (2025-12-19)
"in 3 days"          → Today + 3 days (2025-12-16)
"tomorrow"           → Tomorrow (2025-12-14)
```

#### Smart Assignee Matching
```
Meeting transcript: "Emily should create the dashboard"
Jira users: ["Emily Johnson", "emily@company.com"]
→ Automatically matches and assigns to Emily Johnson
```

## 📂 Project Structure

```
Meeting-Assistant-AI/
├── webapp/                          # Web application
│   ├── backend/                     # FastAPI server
│   │   ├── main.py                  # Application entry
│   │   ├── config.py                # Configuration
│   │   ├── database.py              # Database connection
│   │   ├── db_models.py             # SQLAlchemy models
│   │   ├── models.py                # Pydantic schemas
│   │   ├── auth.py                  # Authentication
│   │   ├── routes/                  # API endpoints
│   │   │   ├── auth.py              # Auth routes
│   │   │   ├── meetings.py          # Meeting CRUD
│   │   │   ├── jira.py              # Jira integration
│   │   │   └── assignees.py         # Assignee mappings
│   │   └── services/
│   │       └── meeting_processor.py # Background processing
│   └── frontend/                    # React application
│       ├── src/
│       │   ├── main.tsx             # Entry point
│       │   ├── App.tsx              # Routes
│       │   ├── api.ts               # API client
│       │   ├── components/          # Reusable components
│       │   ├── context/             # React context (auth)
│       │   └── pages/               # Page components
│       └── package.json
│
├── speech_recognition/              # Transcription module
│   ├── transcriber.py               # Main transcriber
│   ├── core/
│   │   ├── config.py                # Configuration
│   │   └── meeting_transcriber.py  # Meeting-specific logic
│   ├── models/
│   │   ├── whisper_model.py         # Whisper integration
│   │   └── diarization_model.py    # Speaker diarization
│   └── utils/                       # Helper utilities
│
├── summarization/                   # Summarization module
│   ├── summarizer.py                # Main summarizer
│   ├── core/
│   │   └── meeting_summarizer.py   # Meeting summarization
│   └── llm_summarizer.py            # LLM-based summarization
│
├── action_item_extraction/          # Task extraction module
│   ├── core/
│   │   └── task_extractor.py       # Main extractor
│   ├── utils/
│   │   ├── confidence_model.py     # Confidence scoring
│   │   ├── date_parser.py          # Date parsing
│   │   ├── person_extractor.py     # Assignee extraction
│   │   ├── semantic_dedup.py       # Deduplication
│   │   ├── task_patterns.py        # Task patterns
│   │   └── llm_fallback.py         # LLM clarification
│   ├── COMPARISON.md                # Before/after analysis
│   └── README.md                    # Module documentation
│
├── outputs/                         # Generated outputs
│   ├── transcription/               # Transcripts
│   ├── summarization/               # Summaries
│   └── action_items/                # Tasks
│
├── .env                             # Environment variables
├── requirements.txt                 # Python dependencies
└── README.md                        # This file
```

## 🔒 Security

- **Password Hashing**: bcrypt with salt
- **JWT Tokens**: 24-hour expiration
- **CORS Protection**: Configured for localhost dev
- **SQL Injection**: Prevented via SQLAlchemy ORM
- **XSS Protection**: React auto-escaping
- **API Token Storage**: Encrypted in PostgreSQL

## 🐛 Troubleshooting

### Common Issues

**Backend won't start**
```bash
# Check PostgreSQL
pg_isready

# Verify DATABASE_URL in .env
# Check logs for specific errors
```

**Frontend build fails**
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
```

**Groq API errors**
```bash
# Verify API key
curl https://api.groq.com/openai/v1/models \
  -H "Authorization: Bearer $GROQ_API_KEY"
```

**Jira integration fails**
- Verify API token at https://id.atlassian.com/manage-profile/security/api-tokens
- Check project key exists and is accessible
- Ensure user has "Create Issues" permission

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Groq](https://groq.com) - Free, fast AI inference
- [Hugging Face](https://huggingface.co) - Open-source NLP models
- [FastAPI](https://fastapi.tiangolo.com) - Modern Python web framework
- [React](https://react.dev) - UI library
- [Atlassian](https://www.atlassian.com) - Jira API documentation

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/erenculhaci/Meeting-Assistant-AI/issues)
- **Email**: culhaci22@itu.edu.tr or erenculhaci@gmail.com

---

**Made with ❤️ by Eren Culhaci**

