# UI Contract: PDF Download Buttons

## Summary Tab — Download PDF (existing button, behavior change)

**Location**: `frontend-2/app/(dashboard)/meetings/[id]/page.tsx` — inside SummaryMenu dropdown

**Current behavior**: Calls `exportSummaryAsPDF(meeting)` client-side via pdfmake
**New behavior**: Makes authenticated GET request to `/api/v1/meetings/{id}/export/pdf?type=summary`, receives PDF blob, triggers browser download

**Visibility rules** (unchanged):
- Show when: `meeting.status === "completed"`
- Hide when: meeting is processing or failed

**On click**:
1. Call API endpoint with Axios (`responseType: 'blob'`)
2. Create temporary object URL from blob
3. Trigger download via programmatic anchor click
4. Revoke object URL
5. Fire PostHog event `summary_exported` with `{ meeting_id }`

**Error handling**: If API returns error, show toast/alert with error message.

---

## Transcript Tab — Download PDF (existing button, behavior change)

**Location**: `frontend-2/app/(dashboard)/meetings/[id]/page.tsx` — above transcript viewer, aligned right

**Current behavior**: Calls `exportTranscriptAsPDF(meeting)` client-side via pdfmake
**New behavior**: Makes authenticated GET request to `/api/v1/meetings/{id}/export/pdf?type=transcript`, receives PDF blob, triggers browser download

**Visibility rules** (unchanged):
- Show when: `meeting.status === "completed"` AND `meeting.segments` is non-empty
- Hide when: meeting is processing, failed, or has no segments

**Styling** (unchanged): `text-sm font-medium text-stone-600 hover:text-stone-800 border border-stone-200 rounded-lg hover:bg-stone-50 transition-colors` with `Download` lucide icon

**On click**:
1. Call API endpoint with Axios (`responseType: 'blob'`)
2. Create temporary object URL from blob
3. Trigger download via programmatic anchor click
4. Revoke object URL
5. Fire PostHog event `transcript_exported` with `{ meeting_id }`

**Error handling**: If API returns error, show toast/alert with error message.

**Loading state**: Disable button and show spinner while PDF is being generated (network request in-flight).
