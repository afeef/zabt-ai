# API Contract: Meeting Upload

Directly upload a media file for transcription.

## POST /api/v1/meetings/upload

**Description**: Accepts a multipart/form-data upload, stores it in S3, and starts the transcription pipeline.

### Request

- **Type**: `multipart/form-data`
- **Body**:
  - `file`: `UploadFile` (Required)
  - `title`: `str` (Optional, defaults to filename)

### Response

- **Status**: `201 Created`
- **Body**: [MeetingRead](file:///path/to/zabt-ai/backend/app/models.py)

### Error Responses

- **401 Unauthorized**: Missing or invalid JWT.
- **413 Content Too Large**: File exceeds maximum allowed size.
- **500 Internal Server Error**: Storage or database failure.
