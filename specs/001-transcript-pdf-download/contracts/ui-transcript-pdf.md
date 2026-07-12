# UI Contract: Transcript PDF Download

## Export Function

**Location**: `frontend-2/app/lib/pdf-export.ts`

### `exportTranscriptAsPDF(meeting: Meeting): Promise<void>`

**Input**: A `Meeting` object with populated `segments` and `speakers` fields.

**Behavior**:
1. Dynamically imports pdfmake (client-side only)
2. Builds a PDF document with:
   - **Metadata header**: Meeting title (h1), date, duration, speakers — identical layout to `exportSummaryAsPDF`
   - **Separator line**: Same stone-colored horizontal rule
   - **Transcript body**: For each segment in `meeting.segments`:
     - Speaker name (bold, indigo color) + formatted timestamp (`MM:SS` or `H:MM:SS`)
     - Spoken text as a paragraph below the speaker line
     - Small margin between segments
3. Downloads the file as `{sanitized-title}-transcript.pdf`

**Edge cases**:
- Missing speaker name → display "Unknown Speaker"
- Missing/zero timestamp on first segment → omit timestamp
- Empty segments array → function should not be called (button hidden)

## Button Integration

**Location**: `frontend-2/app/(dashboard)/meetings/[id]/page.tsx`

### Transcript Tab — Download PDF Button

**Visibility rules**:
- Show when: `meeting.status === "completed"` AND `meeting.segments` is non-empty
- Hide when: meeting is processing, failed, or has no segments

**Placement**: Above the transcript viewer, aligned right

**Styling**: Matches existing button patterns — `text-sm font-medium text-stone-600 hover:text-stone-800 border border-stone-200 rounded-lg hover:bg-stone-50 transition-colors` with `Download` lucide icon

**On click**: Calls `exportTranscriptAsPDF(meeting)` and fires PostHog event `transcript_exported` with `{ meeting_id }`
