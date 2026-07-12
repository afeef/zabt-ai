# Quickstart: AI Meeting Assistant

## Prerequisites
- Docker & Docker Compose
- OpenAI API Key (or compatible local LLM URL) set in `.env` as `OPENAI_API_KEY`

## Running Locally

1. **Build Services**:
   ```bash
   docker-compose build
   ```

2. **Start Stack**:
   ```bash
   docker-compose up -d
   ```
   - Frontend: `http://localhost:3000`
   - Backend API: `http://localhost:8000`
   - Worker (Celery): Running in background

3. **Verify Transcription**:
   - Navigate to `http://localhost:3000/dashboard/meetings`
   - Click "New Meeting" -> "Start Recording"
   - Speak into microphone
   - Verify text appears continuously
