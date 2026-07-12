"""PostHog analytics wrapper.

Exposes a thin capture() function so consuming code never imports posthog directly.
All calls fail silently — analytics must never break application or worker flow.
"""

import posthog as ph
from app.core.config import settings

ph.api_key = settings.POSTHOG_API_KEY
ph.host = settings.POSTHOG_HOST


def capture(user_id: str | int, event: str, properties: dict | None = None) -> None:
    """Fire a server-side analytics event tied to user_id."""
    if not settings.POSTHOG_API_KEY:
        return
    try:
        ph.capture(str(user_id), event, properties or {})
    except Exception:
        pass


def shutdown() -> None:
    """Flush buffered events before process exit. Call from lifespan teardown / worker_shutdown."""
    try:
        ph.shutdown()
    except Exception:
        pass
