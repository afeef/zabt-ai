# Quickstart: Meeting Delete Option

This feature introduces no new environment variables, external services, or infrastructure changes. It leverages the existing Postgres Database and Storage mechanisms.

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
pytest tests/e2e/test_meeting_delete.py -v
```
