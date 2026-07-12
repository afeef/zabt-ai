# Quickstart: Supabase DB Migration

## Environment Variables

This feature modifies the **value** of one existing environment variable. No new variables are introduced.

| Variable | Service | Change | Example Value |
|----------|---------|--------|---------------|
| `DATABASE_URL` | api, worker | Value updated to Supabase connection string | `postgresql+asyncpg://postgres.[ref]:[pass]@aws-0-[region].pooler.supabase.com:5432/postgres?sslmode=require` |

## Prerequisites

- Supabase project provisioned with Postgres database
- Direct connection string from Supabase dashboard (Settings → Database → Connection string → URI, port 5432)
- `postgresql-client` installed on VPS (`sudo apt-get install -y postgresql-client`)
- SSH access to the VPS

## Rollback

To rollback to VPS Postgres:

1. Revert `DATABASE_URL` in `.env` to `postgresql+asyncpg://app:app@db:5432/zabt`
2. Remove `profiles: ["local"]` from the `db` service in `docker-compose.yml`
3. Restore `- db` to `depends_on` in `api` and `worker` services
4. Run `docker compose up -d`

The `postgres_data` Docker volume is preserved and contains the original database.
