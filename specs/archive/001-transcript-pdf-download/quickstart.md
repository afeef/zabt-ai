# Quickstart: Download Transcript as PDF

## Prerequisites

- `pdfmake` and `@types/pdfmake` already installed in `frontend-2/`
- No new dependencies needed
- No new environment variables needed
- No backend changes needed

## Dependencies (already present)

| Package | Version | Purpose |
|---------|---------|---------|
| pdfmake | ^0.2.x | Client-side PDF generation |
| @types/pdfmake | ^0.2.x | TypeScript types (dev) |

## Test Scenario

1. Start the frontend: `cd frontend-2 && npm run dev`
2. Log in and navigate to a completed meeting with transcript data
3. Switch to the Transcript tab
4. Click "Download PDF" button
5. Verify:
   - PDF file downloads with filename `{meeting-title}-transcript.pdf`
   - PDF contains metadata header (title, date, duration, speakers)
   - PDF contains all transcript segments with speaker names and timestamps
   - Long transcripts paginate correctly
   - Special characters in meeting title are sanitized in filename

## E2E Test

```bash
pytest tests/e2e/test_transcript_pdf.py -v
```

Required environment variables for E2E:
- `FRONTEND_URL` (default: `http://localhost:3000`)
- `TEST_USER_EMAIL`
- `TEST_USER_PASSWORD`
- `TEST_MEETING_ID` — ID of a completed meeting with transcript segments
