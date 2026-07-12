# Research: Supabase DB Migration

## Decision: Connection Mode

- **Decision**: Direct connection (port 5432), not Supavisor pooler (port 6543)
- **Rationale**: API and worker are long-running processes with their own asyncpg connection pools. Direct connections avoid pooler quirks (e.g., prepared statement incompatibility with transaction-mode pooling).
- **Alternatives considered**: Supavisor pooler — better for serverless/ephemeral connections, but unnecessary for our long-lived containers.

## Decision: Dump/Restore Tool

- **Decision**: `pg_dump -F custom` + `pg_restore` with `--no-owner --no-privileges`
- **Rationale**: Custom format is fastest for restore, supports selective table restore if needed, and handles large objects. `--no-owner` is required because Supabase uses a different role system than the VPS container.
- **Alternatives considered**: Plain SQL dump (`pg_dump -F plain`) — simpler but slower for large databases and no selective restore capability. `pg_dumpall` — not needed since we only have one database.

## Decision: SSL Mode

- **Decision**: `sslmode=require` appended to DATABASE_URL
- **Rationale**: Supabase enforces SSL on all connections. Without it, asyncpg will fail to connect.
- **Alternatives considered**: `sslmode=verify-full` — more secure but requires downloading Supabase's CA certificate and configuring asyncpg with it. Overkill for this setup since Supabase endpoints are already HTTPS-only.

## Decision: Firewall (UFW)

- **Decision**: No UFW changes needed
- **Rationale**: VPS UFW config shows `Default: allow (outgoing)`. Docker containers use NAT through the host's network stack, so outbound connections from containers to Supabase (port 5432) are already permitted.
- **Alternatives considered**: Explicit `ufw allow out 5432/tcp` — redundant since outbound is already allowed by default policy.

## Decision: Postgres Version Compatibility

- **Decision**: Proceed with pg_dump from Postgres 16 (VPS) → restore to Postgres 15 (Supabase)
- **Rationale**: pg_dump custom format is backward-compatible. The current schema uses no Postgres 16-specific features (confirmed by reviewing Alembic migrations — all standard SQL types and constraints).
- **Alternatives considered**: Requesting Supabase upgrade to Postgres 16 — unnecessary complexity for a compatible schema.
