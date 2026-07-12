# Data Model: Supabase Auth & Repurposed Backend

## Supabase User (Frontend & Abstract Backend)
_Managed entirely by the Supabase Hosted Auth service. The backend only references the generated UUID._

- **id**: UUID (Primary Key from Supabase)
- **email**: String
- **created_at**: Timestamp

## AI Task (Backend PostgreSQL)
_Records of transcriptions and summaries processed by the FastAPI service._

- **id**: UUID (Primary Key)
- **user_id**: UUID (Foreign Key loosely coupled to the `sub` claim of the Supabase JWT)
- **task_type**: Enum (`TRANSCRIPTION`, `SUMMARIZATION`)
- **status**: Enum (`PENDING`, `PROCESSING`, `COMPLETED`, `FAILED`)
- **input_reference**: String (URL or pointer to audio/text input)
- **result_output**: Text/JSON (The final transcribed or summarized text)
- **created_at**: Timestamp
- **updated_at**: Timestamp

## Relationships
- One **Supabase User** has many **AI Tasks**.

## Validation Rules
- `user_id` MUST be extracted directly from the verified Supabase JWT; it cannot be supplied in the request body to prevent spoofing.
- The backend MUST verify the JWT signature using the `SUPABASE_JWT_SECRET` prior to acting upon any data associated with a `user_id`.
