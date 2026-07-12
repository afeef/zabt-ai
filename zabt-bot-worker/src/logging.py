"""Centralized logging with Sentry + Logfire."""

import logging
import sys

from src.config import settings


def _get_formatter() -> logging.Formatter:
    return logging.Formatter(
        "%(asctime)s [%(levelname)s] %(module)s:%(lineno)d - %(message)s"
    )


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(_get_formatter())
        logger.setLevel(logging.INFO)
        logger.addHandler(handler)
        logger.propagate = False
    return logger


def init_sentry() -> None:
    if not settings.SENTRY_DSN:
        return
    import sentry_sdk
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.SENTRY_ENVIRONMENT,
        traces_sample_rate=1.0,
    )


def init_logfire() -> None:
    if not settings.LOGFIRE_TOKEN:
        return
    import logfire
    logfire.configure(
        service_name="zabt-bot-worker",
        send_to_logfire="if-token-present",
    )
