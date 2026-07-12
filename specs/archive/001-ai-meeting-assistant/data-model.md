# Data Model: Enterprise AI Meeting Assistant

**Status**: Phase 1 Design
**Feature**: `001-ai-meeting-assistant`

## Entities

### User (Managed by Logto)
- Identity Management, Passwords, and Sessions are handled by Logto.
- **local_user_mapping**: We will map `logto_user_id` (Subject ID) to our internal data if needed, or index by it directly.
- **Roles**: Defined in Logto (Admin, User, ComplianceOfficer) and synced via ID Token claims.


### Meeting
- **id**: UUID
- **user_id**: UUID (FK)
- **title**: String
- **start_time**: DateTime
- **end_time**: DateTime (Nullable)
- **status**: Enum (Recording, Processing, Completed, Failed)
- **audio_url**: String (Path to stored file)
- **created_at**: DateTime

### TranscriptSegment
- **id**: UUID
- **meeting_id**: UUID (FK)
- **start_time**: Float (Offset in seconds)
- **end_time**: Float (Offset in seconds)
- **text**: String
- **speaker**: String (Optional)

### MeetingNote
- **id**: UUID
- **meeting_id**: UUID (FK)
- **note_type**: Enum (Minutes, ActionItems, Retrospective, Email)
- **content**: Text (Markdown)
- **generated_at**: DateTime

### StyleProfile
- **id**: UUID
- **user_id**: UUID (FK)
- **name**: String
- **description**: String
- **example_content**: Text (Extracted structure from PDF)
- **is_default**: Boolean

## Relationships

- User `1:N` Meeting
- User `1:N` StyleProfile
- Meeting `1:N` TranscriptSegment
- Meeting `1:N` MeetingNote

## Persistence

- **Database**: PostgreSQL (SQLModel/SQLAlchemy)
- **File Storage**: Local filesystem `/media/recordings/{user_id}/{meeting_id}.{ext}` (Encrypted).
- **Cache**: Redis for real-time transcript buffers.
