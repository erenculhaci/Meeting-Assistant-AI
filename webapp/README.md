# Meeting Assistant AI - Web Application

Modern web interface for meeting transcription, summarization, and task extraction.

## Features

- 🎤 **Upload & Transcribe**: Upload audio/video files for automatic transcription
- 📝 **AI Summarization**: Get intelligent meeting summaries with key points
- ✅ **Task Extraction**: Automatically extract action items from meetings
- 🔗 **Jira Integration**: Create Jira issues directly from extracted tasks
- 👥 **User Mapping**: Map meeting participants to Jira users

## Tech Stack

- **Backend**: FastAPI (Python)
- **Frontend**: React + TypeScript + Tailwind CSS
- **AI**: Groq Whisper (transcription) + LLM (summarization & extraction)

## Quick Start

### 1. Install Backend Dependencies

```bash
cd webapp/backend
pip install -r requirements.txt
```

### 2. Install Frontend Dependencies

```bash
cd webapp/frontend
npm install
```

### 3. Start Backend Server

```bash
cd webapp/backend
python main.py
# or
uvicorn main:app --reload --port 8000
```

### 4. Start Frontend Dev Server

```bash
cd webapp/frontend
npm run dev
```

### 5. Open Application

Visit http://localhost:5173 in your browser.

## API Endpoints

### Meeting Processing
- `POST /api/upload` - Upload and process audio/video file
- `GET /api/jobs/{job_id}` - Get job status
- `GET /api/results/{job_id}` - Get processing results
- `GET /api/results` - List all results

### Jira Integration
- `POST /api/jira/config` - Save Jira configuration
- `GET /api/jira/config` - Get current configuration
- `GET /api/jira/users` - Get Jira users
- `GET /api/jira/projects` - Get Jira projects
- `POST /api/jira/user-mappings` - Save user mapping
- `POST /api/jira/create-issues` - Create Jira issues

## Environment Variables

Make sure you have a `.env` file in the project root with:

```
GROQ_API_KEY=your_groq_api_key
```

## Jira Setup

1. Go to https://id.atlassian.com/manage-profile/security/api-tokens
2. Create a new API token
3. In the app, go to Settings and enter:
   - Your Jira domain (e.g., `yourcompany.atlassian.net`)
   - Your email address
   - The API token
   - Your project key (e.g., `PROJ`)

## License

MIT
