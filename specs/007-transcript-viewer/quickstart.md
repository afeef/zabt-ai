# Quickstart: Transcript Viewer

This feature introduces no new environment variables or infrastructure changes. It leverages the existing Postgres Database, Redis queue, and Supabase Storage mechanisms.

## Local Test Setup

1. Start exactly as usual:
```bash
docker-compose up -d db redis
```

2. Start the Backend API (Terminal 1)
```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload
```

3. Start the Frontend (Terminal 2)
```bash
cd frontend-2
npm install
npm run dev
```

## E2E Testing Verification

Following Zabt's constitution, verifying this feature locally requires Playwright:

```bash
cd backend
source .venv/bin/activate
pip install -r requirements-dev.txt
playwright install chromium
pytest tests/e2e/test_transcript_viewer.py -v
```

### Mocking Data
Because local generation of 30+ minute WhisperX transcripts is extremely slow, test payloads simulating `SPEAKER_00` and `SPEAKER_01` crossing the 30-minute threshold must be mocked within the Playwright network interception routes.
