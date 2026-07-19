# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2025-2026 Afeef Janjua
from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.core.config import settings
from app.core.logging import init_sentry, init_logfire
from app.middleware.audit import AuditMiddleware
from app.db.engine import create_db_and_tables

init_sentry()
init_logfire(service_name="zabt-api")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load database on startup (for dev simplicity, usually use alembic)
    create_db_and_tables()
    from app.services.template_seed import seed_built_in_templates
    seed_built_in_templates()
    yield
    from app.services.analytics import shutdown as analytics_shutdown
    analytics_shutdown()

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# CORS — allow frontend-2 origin (http://localhost:3000 for development)
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.BACKEND_CORS_ORIGINS.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(AuditMiddleware)

# Logfire auto-instrumentation (live request tracing, DB queries, outgoing HTTP)
if settings.LOGFIRE_TOKEN:
    import logfire
    from app.db.engine import engine
    from app.core import otel_patch

    # OTEL's FastAPI route extraction crashes on Starlette 1.x included routers
    # (see app/core/otel_patch.py). Patch it BEFORE instrumenting so request
    # tracing works instead of 500-ing on routes like /api/v1/meetings/.
    otel_patch.apply()

    logfire.instrument_fastapi(app)
    logfire.instrument_sqlalchemy(engine=engine)
    logfire.instrument_httpx()
    logfire.instrument_celery()

from app.api.api import api_router
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
async def root():
    return {"message": "Welcome to Zabt API", "docs": "/docs"}
