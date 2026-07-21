# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2025-2026 Afeef Janjua

from sqlmodel import SQLModel, create_engine
from app.core.config import settings

# Correct connection string for asyncpg
DATABASE_URL = str(settings.DATABASE_URL)

# Use SSL for external databases (Supabase etc.) — skip for local Docker container
_sync_url = DATABASE_URL.replace("+asyncpg", "")
_connect_args = {}
# TCP keepalives detect a half-open (silently reaped) connection and surface it
# as OperationalError instead of blocking recv() forever — guards any query that
# lands on a connection Supavisor/NAT dropped mid-flight. Dead-peer detection is
# roughly keepalives_idle + keepalives_interval * keepalives_count (~= 60s).
_connect_args["keepalives"] = 1
_connect_args["keepalives_idle"] = 30
_connect_args["keepalives_interval"] = 10
_connect_args["keepalives_count"] = 3
_connect_args["connect_timeout"] = 10
# NOTE: a server-side idle_in_transaction_session_timeout backstop was considered
# but deliberately dropped from this hotfix. Delivering it via the libpq startup
# `options` packet risks failing every connection app-wide if Supavisor session
# mode rejects the startup parameter, and keepalives + connect_timeout +
# expire_on_commit=False + the Celery time_limit already close the traced hang.
# If added later, deliver it via a post-connect `SET` (event.listens_for(engine,
# "connect")), never the startup packet.
if "supabase.co" in DATABASE_URL or "pooler.supabase.com" in DATABASE_URL:
    _connect_args["sslmode"] = "require"

# pool_pre_ping issues a cheap SELECT 1 before each checkout, so stale
# connections killed by Supabase's Supavisor idle timeout are transparently
# replaced instead of surfacing as "SSL connection has been closed unexpectedly".
# pool_recycle bounds connection age to 5 min as defense-in-depth.
# See Sentry ZABT-API-1D / 1G / 1Y.
engine = create_engine(
    _sync_url,
    echo=False,
    connect_args=_connect_args,
    pool_pre_ping=True,
    pool_recycle=300,
)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
