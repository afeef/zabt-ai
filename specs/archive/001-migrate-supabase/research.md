# Research: Migrate Auth to Supabase Cloud & Repurpose Backend

## 1. Frontend Integration with Supabase
- **Decision**: Use `@supabase/supabase-js` and `@supabase/ssr` in the Next.js frontend to handle Auth.
- **Rationale**: This is the official and most up-to-date Supabase Auth approach for Next.js App Router. It automatically handles session cookies, JWT token rotation, and provides React hooks and server-side utilities.
- **Alternatives considered**: NextAuth.js (Auth.js) - Rejected because using Supabase's native client provides a more direct integration with their ecosystem and enables potential future use of Supabase Realtime or Storage.

## 2. FastAPI JWT Verification
- **Decision**: FastAPI will use `python-jose` (or `PyJWT`) to verify the `access_token` sent by the frontend via the `Authorization: Bearer <token>` header, signed by the Supabase project's JWT secret.
- **Rationale**: Since the backend will no longer handle auth registration or login, it simply needs to act as a resource server. Verifying the HS256 JWT locally using the shared Superbase JWT secret is extremely fast and doesn't require outward network calls to Supabase on every AI request. 
- **Alternatives considered**: Using the unofficial `supabase-py` client to handle user fetching. Rejected because we only need stateless JWT validation for protecting the AI endpoints, keeping the backend lightweight.

## 3. Local Infrastructure Reduction
- **Decision**: Remove the `logto` and `logto-db` (if distinct) or Logto-related tables from `docker-compose.yml`. Only the core Postgres database (if retained for AI metadata) and Redis (if used) will run locally.
- **Rationale**: Adheres to the user's specification that "The local docker-compose will no longer run auth services", lowering CPU and RAM usage.
- **Alternatives considered**: Replacing Logto with local GoTrue containers. Rejected because the spec explicitly dictates using "Hosted Supabase" to reduce local overhead.

## 4. Repurposing the Backend
- **Decision**: Delete all login/registration logic in `backend/app/api/v1/endpoints/auth.py`. Expose purely AI-bound routes (e.g., `/api/v1/ai/transcribe`, `/api/v1/ai/summarize`) that depend on a `get_current_user` dependency.
- **Rationale**: Matches the new strictly-bounded context of the FastAPI service under the updated constitution.
- **Alternatives considered**: Keeping a shadow user table in the backend. Rejected as unnecessary since the JWT contains the `sub` (User ID) and `email`, which is sufficient for scoping AI task execution.
