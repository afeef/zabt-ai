# Quickstart: Supabase & AI Backend Setup

## 1. Environment Variables

Add the following to your frontend `.env.local`:

```bash
# Frontend Next.js (.env.local)
NEXT_PUBLIC_SUPABASE_URL=https://<project-ref>.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=<your-supabase-anon-key>
```

Add the following to your backend `.env`:

```bash
# FastAPI Backend (.env)
SUPABASE_URL=https://<project-ref>.supabase.co
SUPABASE_JWT_SECRET=super-secret-jwt-token-with-at-least-32-characters-long
```

## 2. Infrastructure Changes

- **Logto Removed**: Run `docker-compose down` to stop all containers, then execute `docker-compose up -d` after pulling the newest `docker-compose.yml`. The logto containers and their associated DB networks have been excised to save memory.
- **Frontend Running**: Start the frontend independently pointing to the remote Supabase URL via the environment variables. The Nextjs app connects to Supabase directly for registration and login.
- **Backend Running**: The backend FastAPI server runs locally. When you test an AI transcription route via cURL, Postman, or the frontend, ensure you extract the user's `access_token` from their Supabase session and pass it into the `Authorization` header as `Bearer <token>`. FastAPI uses the `SUPABASE_JWT_SECRET` to validate the token without making a network call.
