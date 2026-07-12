# Quickstart: Meeting Upload Progress

**Feature**: 001-meeting-upload  
**Date**: 2026-02-22

---

## Environment Variables

This feature relies entirely on existing authentication and API configuration. No new environment variables are required.

| Variable | Purpose | Location |
|----------|---------|----------|
| `NEXT_PUBLIC_API_URL` | Base URL for the Axios client `POST /api/v1/meetings/upload` | `frontend-2/.env` |

## Local Development Setup

To test the upload flow locally:

1. **Ensure Backend & Redis/Worker are running**:
   Since uploading a file triggers the Celery worker to begin transcription, you need the full stack running to verify backend acceptance.
   ```bash
   docker compose up -d
   ```

2. **Run the Frontend**:
   ```bash
   cd frontend-2
   npm run dev
   ```

3. **Log in**: 
   Access the app at `http://localhost:3000`, log in, and click "Upload a meeting" from the dashboard right panel.

## E2E Testing

To run the Playwright test suite for the upload modal:

```bash
cd tests/e2e
pytest test_meeting_upload.py -v
```

### Test Scope:
- Validates the modal opens when clicking upload.
- Validates the file picker interactions.
- Validates the UI progress elements render.
- Validates cancellation UI flow.
