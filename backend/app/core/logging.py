"""Centralized logging and Sentry initialization.

Provides get_logger(name) for consistent logging across the application.
Sentry auto-captures ERROR+ log messages when initialized — no explicit handler needed.
"""

import logging
import sys

from app.core.config import settings


def _get_log_level() -> int:
    """DEBUG for local dev, WARNING for production."""
    if settings.SENTRY_ENVIRONMENT in ("local", "development"):
        return logging.DEBUG
    return logging.WARNING


def _get_formatter() -> logging.Formatter:
    return logging.Formatter(
        "%(asctime)s [%(levelname)s] %(module)s:%(lineno)d - %(message)s"
    )


def _get_console_handler() -> logging.StreamHandler:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(_get_formatter())
    return handler


def get_logger(name: str) -> logging.Logger:
    """Return a configured logger with console output.

    Sentry automatically captures ERROR+ messages when sentry_sdk is initialized.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(_get_log_level())
        logger.addHandler(_get_console_handler())
        logger.propagate = False
    return logger


def init_sentry() -> None:
    """Initialize Sentry SDK if SENTRY_DSN is configured. No-ops otherwise."""
    if not settings.SENTRY_DSN:
        return
    import sentry_sdk

    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.SENTRY_ENVIRONMENT,
        traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
        send_default_pii=False,
        enable_logs=True,
    )


def init_logfire(service_name: str = "zabt-api") -> None:
    """Initialize Logfire structured tracing if LOGFIRE_TOKEN is configured. No-ops otherwise."""
    if not settings.LOGFIRE_TOKEN:
        return
    import logfire

    logfire.configure(
        service_name=service_name,
        send_to_logfire="if-token-present",
    )
