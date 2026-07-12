"""Regression tests for Settings class defaults.

These tests lock in the zabt.ai domain defaults so a future edit
can't accidentally regress them to a different domain.

We read class-level defaults via `Settings.model_fields[<name>].default`
rather than instantiating Settings(), so any env vars set on the host
running the tests can't interfere with the assertions.

Run with: ``uv run pytest tests/unit/test_config_defaults.py --noconftest``
The ``--noconftest`` flag is required because ``tests/conftest.py`` imports
``app.main`` at module level, which triggers SQLAlchemy engine creation
requiring a valid DATABASE_URL. That's a pre-existing infrastructure
quirk unrelated to this test file.
"""
from app.core.config import Settings


class TestDomainDefaults:
    """Default values that reference the primary product domain."""

    def test_app_url_default_is_app_zabt_ai(self):
        default = Settings.model_fields["APP_URL"].default
        assert default == "https://app.zabt.ai", (
            f"APP_URL default regressed: {default!r}. "
            "It must point at the new frontend host. See "
            "docs/superpowers/specs/2026-04-11-zabt-ai-domain-migration-design.md"
        )

    def test_resend_from_email_default_is_zabt_ai(self):
        default = Settings.model_fields["RESEND_FROM_EMAIL"].default
        assert default == "no-reply@zabt.ai", (
            f"RESEND_FROM_EMAIL default regressed: {default!r}. "
            "It must use the new sending domain."
        )

    def test_microsoft_redirect_uri_default_is_empty(self):
        # The default stays empty; the VPS .env must set it explicitly.
        # This test ensures the field exists and is not hardcoded to any URL.
        default = Settings.model_fields["MICROSOFT_REDIRECT_URI"].default
        assert default == "", (
            f"MICROSOFT_REDIRECT_URI should have an empty default "
            f"(got {default!r}). The VPS .env must set it explicitly."
        )
