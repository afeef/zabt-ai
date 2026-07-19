# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2025-2026 Afeef Janjua
"""Compatibility shim for opentelemetry-instrumentation-fastapi on Starlette 1.x.

OTEL 0.63b1's ``_get_route_details`` does ``route = starlette_route.path`` while
iterating ``app.routes``. On Starlette 1.x, ``app.routes`` can contain
``_IncludedRouter`` entries (from ``include_router``) that have no ``.path``,
so the attribute access raises ``AttributeError`` and every request whose match
resolves to an included router returns HTTP 500 (e.g. ``/api/v1/meetings/``).

This replaces ``_get_route_details`` with a version that recurses into nested
routers to recover the matched leaf route template, and is fully defensive: any
failure returns ``None`` (OTEL then falls back to a generic span name). It can
only affect span naming — never request handling.

Remove once opentelemetry-instrumentation-fastapi ships Starlette 1.x support.
"""
from __future__ import annotations

from app.core.logging import get_logger

logger = get_logger(__name__)


def _resolve_route(routes, scope):
    """Return the matched leaf route template (best effort), or None."""
    from starlette.routing import Match

    best = None
    for route in routes:
        try:
            match, child_scope = route.matches(scope)
        except Exception:
            continue
        if match is Match.NONE:
            continue
        # An included router / mount exposes its own path (or prefix) plus children.
        prefix = getattr(route, "path", None) or getattr(route, "prefix", "") or ""
        children = getattr(route, "routes", None)
        if children:
            merged = dict(scope)
            if isinstance(child_scope, dict):
                merged.update(child_scope)
            sub = _resolve_route(children, merged)
            if sub is not None:
                return f"{prefix}{sub}" if prefix else sub
        if match is Match.FULL and prefix:
            return prefix
        if best is None and prefix:
            best = prefix
    return best


def _safe_get_route_details(scope):
    try:
        app = scope.get("app")
        if app is None:
            return None
        return _resolve_route(app.routes, scope)
    except Exception:  # never let tracing break a request
        return None


def apply() -> None:
    """Patch OTEL's FastAPI route extraction. Safe to call more than once."""
    try:
        import opentelemetry.instrumentation.fastapi as otel_fastapi

        if getattr(otel_fastapi, "_get_route_details", None) is _safe_get_route_details:
            return
        if hasattr(otel_fastapi, "_get_route_details"):
            otel_fastapi._get_route_details = _safe_get_route_details
            logger.info("Applied OTEL FastAPI route-details Starlette-1.x compatibility patch")
    except Exception as exc:  # patch failure must not break startup
        logger.warning("Could not apply OTEL FastAPI compatibility patch: %s", exc)
