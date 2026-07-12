# Compose Fragments

This directory holds Docker Compose overlay files. They are combined via the
`COMPOSE_FILE` env var (read from `.env` automatically by Docker Compose).

## Files

- `prod.yml` — production overlay. Adds Kong gateway, mounts SSL certs,
  applies prod URL overrides. Used on the VPS.
- `local.yml` — local overlay. Adds the Next.js dev container, exposes the
  API on `:8000`, applies localhost URL overrides. No Kong.
- `db.local.yml` — opt-in. Adds a Postgres container on `:5433` and overrides
  `DATABASE_URL` on api/worker/beat. Omit to use Supabase from `.env`.
- `storage.local.yml` — opt-in. Adds MinIO + bucket initializer and sets
  `STORAGE_PROVIDER=minio` on api/worker. Omit to use S3 from `.env`.
- `gpu.local.yml` — opt-in. Adds the local GPU worker on `:8001` and sets
  `TRANSCRIPTION_BACKEND=gpu-local` on worker. Omit to use RunPod from `.env`.
- `prod.env.example` — starter `.env` for the VPS.
- `local.env.example` — starter `.env` for local dev (full standalone stack).

## Decision tree for new services

1. Runs in every environment? → add stanza to `docker-compose.yml`.
2. Needs prod-specific overrides? → add additive stanza to `compose/prod.yml`.
3. Local stand-in for a cloud service? → new `compose/<thing>.local.yml`
   that includes both the container and the env overrides pointing at it.
4. Local-dev-only with no cloud equivalent (like the Next.js dev server)?
   → add to `compose/local.yml`.

A service can be in (1) AND (2). Otherwise pick exactly one of (3) or (4).
No `profiles:` anywhere.

## Common invocations

```bash
# Production (VPS) — first time:
cp compose/prod.env.example .env
# Edit .env to fill secrets, then:
docker compose up -d --build

# Local — full standalone (GPU box, no cloud deps):
cp compose/local.env.example .env
docker compose up

# Local — dev against cloud (laptop, no GPU). Edit COMPOSE_FILE in .env to:
#   COMPOSE_FILE=docker-compose.yml:compose/local.yml
docker compose up

# One-shot mix without editing .env:
COMPOSE_FILE=docker-compose.yml:compose/local.yml:compose/db.local.yml docker compose up
```

See `docs/superpowers/specs/2026-04-26-compose-restructure-design.md` for
the full design rationale.
