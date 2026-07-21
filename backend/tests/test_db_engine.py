# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2025-2026 Afeef Janjua
"""Guardrails for the sync engine's pool configuration.

Regressing any of these silently brings back
``psycopg2.OperationalError: SSL connection has been closed unexpectedly``
on the first DB query after an idle period (Sentry ZABT-API-1D / 1G / 1Y).
"""
from app.db.engine import engine


def test_pool_pre_ping_enabled() -> None:
    assert engine.pool._pre_ping is True, (
        "pool_pre_ping must be True so stale Supavisor-killed connections "
        "are detected and replaced before being handed to a caller."
    )


def test_pool_recycle_set_under_supavisor_idle_window() -> None:
    assert engine.pool._recycle == 300, (
        "pool_recycle must be set so connections are proactively replaced "
        "inside Supavisor's idle-timeout window."
    )


def test_echo_disabled_in_production_config() -> None:
    assert engine.echo is False, (
        "echo must be False — SQL statement logging belongs to Logfire/Sentry, "
        "not SQLAlchemy's debug echo."
    )


from app.db.engine import _connect_args


def test_tcp_keepalives_configured() -> None:
    # Keepalives make a half-open (silently reaped) socket surface as
    # OperationalError instead of blocking recv() forever — the primary
    # guard against the 2026-07-21 sync_calendars hang.
    assert _connect_args.get("keepalives") == 1
    assert _connect_args.get("keepalives_idle") == 30
    assert _connect_args.get("keepalives_interval") == 10
    assert _connect_args.get("keepalives_count") == 3


def test_connect_timeout_configured() -> None:
    assert _connect_args.get("connect_timeout") == 10


def test_no_startup_options_packet() -> None:
    # idle_in_transaction_session_timeout was intentionally NOT delivered via the
    # libpq startup `options` packet: on the shared app engine a Supavisor
    # rejection would fail every connection app-wide. If a server-side timeout is
    # ever reintroduced, it must be a post-connect SET, not a startup option.
    assert "options" not in _connect_args
