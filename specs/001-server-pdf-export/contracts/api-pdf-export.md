# API Contract: PDF Export Endpoint

## GET /api/v1/meetings/{meeting_id}/export/pdf

**Description**: Generate and download a PDF for a meeting's summary or transcript.

### Request

**Path Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| meeting_id | integer | Yes | The meeting ID |

**Query Parameters**:
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| type | string | Yes | — | Export type: `"summary"` or `"transcript"` |

**Headers**:
| Header | Required | Description |
|--------|----------|-------------|
| Authorization | Yes | `Bearer <supabase_jwt_token>` |

### Success Response

**Status**: `200 OK`

**Headers**:
| Header | Value |
|--------|-------|
| Content-Type | `application/pdf` |
| Content-Disposition | `attachment; filename="{sanitized-title}-{type}.pdf"` |

**Body**: Raw PDF bytes

### Error Responses

| Status | Condition | Body |
|--------|-----------|------|
| 400 | Invalid `type` parameter (not `summary` or `transcript`) | `{"detail": "Invalid export type. Must be 'summary' or 'transcript'."}` |
| 400 | Transcript PDF requested but meeting has no segments | `{"detail": "Meeting has no transcript segments."}` |
| 400 | Meeting status is not `completed` | `{"detail": "PDF export is only available for completed meetings."}` |
| 401 | Missing or invalid JWT token | `{"detail": "Not authenticated"}` |
| 403 | User does not own the meeting | `{"detail": "Not enough permissions"}` |
| 404 | Meeting not found | `{"detail": "Meeting not found"}` |
| 500 | PDF generation failed | `{"detail": "Failed to generate PDF. Please try again."}` |

### PDF Content Structure

**Summary PDF**:
1. Metadata header: meeting title (large heading), date, duration, speaker names
2. Horizontal separator line
3. Summary body: markdown rendered with headings, lists, bold, italic preserved
4. Action items section (if action_items_text exists)

**Transcript PDF**:
1. Metadata header: meeting title (large heading), date, duration, speaker names
2. Horizontal separator line
3. Transcript body: for each segment — speaker name (bold, indigo color) + timestamp (gray), then spoken text below

**Multilingual**:
- Arabic/Urdu text: rendered RTL with `dir="rtl"` applied per block
- Devanagari/Hindi text: rendered LTR with proper conjunct characters
- Mixed scripts: each block gets appropriate direction based on content detection
