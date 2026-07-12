# Quickstart: Server-Side PDF Export

## Prerequisites

- Python 3.11 with `uv` package manager
- Docker (for running the backend)
- Node.js 20 (for frontend-2)

## New Dependencies

### Backend (Python)
```
weasyprint>=68.0    # HTML/CSS → PDF generation
mistune>=3.0        # Markdown → HTML conversion
```

### Backend (System packages in Dockerfile)
```
libpango-1.0-0       # Pango text layout (runtime)
libpangoft2-1.0-0    # Pango FreeType integration (runtime)
libharfbuzz-subset0   # HarfBuzz font subsetting (runtime)
libharfbuzz0b         # HarfBuzz text shaping (runtime)
fonts-noto-core       # Noto fonts for multilingual rendering
```

### Frontend (removals)
```
pdfmake              # REMOVE — no longer needed
@types/pdfmake       # REMOVE — no longer needed
```

## Environment Variables

No new environment variables required. The PDF export endpoint uses the existing Supabase JWT authentication.

## Testing Scenarios

### Summary PDF Export
1. Start backend: `cd backend && uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`
2. Start frontend: `cd frontend-2 && npm run dev`
3. Log in and navigate to a completed meeting
4. On the Summary tab, click "Download PDF" in the menu
5. Verify: PDF downloads with meeting title, date, duration, speakers, and formatted summary

### Transcript PDF Export
1. Navigate to a completed meeting with transcript segments
2. Switch to the Transcript tab
3. Click "Download PDF" button
4. Verify: PDF downloads with speaker labels, timestamps, and spoken text

### Multilingual Rendering
1. Navigate to a meeting with Urdu/Arabic or Hindi content
2. Download summary and transcript PDFs
3. Verify: Arabic script renders RTL with proper ligatures; Devanagari renders with correct conjuncts; no empty boxes or garbled characters

### Error Cases
- Try downloading PDF for a processing meeting → button should not be visible
- Try accessing endpoint directly for another user's meeting → 403 error
- Try requesting transcript PDF for a meeting with no segments → 400 error
