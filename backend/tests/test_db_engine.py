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
