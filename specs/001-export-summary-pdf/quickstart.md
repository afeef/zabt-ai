# Quickstart: Export Summary as PDF

**Feature**: `001-export-summary-pdf`

## Prerequisites

No new environment variables required. This feature is purely client-side.

## Install dependency

```bash
cd frontend-2
npm install pdfmake
npm install --save-dev @types/pdfmake
```

## Running locally

No changes to the backend or docker-compose are needed.

```bash
cd frontend-2 && npm run dev
```

Navigate to any completed meeting (`/meetings/{id}`) → click the `···` summary menu → "Download as PDF".

## Verify the output

1. The PDF file downloads automatically (check browser's downloads folder).
2. Open the PDF — verify the header shows the meeting title, date, and speakers.
3. Verify the summary body is readable with formatted headings and lists (not raw markdown symbols).
4. Verify the filename matches `{meeting-title}-summary.pdf` with no invalid characters.

## Type-check

```bash
cd frontend-2 && npx tsc --noEmit
```
