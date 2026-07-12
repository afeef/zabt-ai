# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2025-2026 Afeef Janjua
"""
E2E Test: Home AI Query Bar

Tests that submitting the AI query bar on the home page routes the user
to /meetings with the query string pre-populated.

Requirements:
    pip install playwright pytest-playwright
    playwright install chromium

Run:
    pytest tests/e2e/test_home_ai_query.py -v
"""

import os
import pytest
from playwright.sync_api import Page, expect

BASE_URL = os.environ.get("FRONTEND_URL", "http://localhost:3000")
TEST_EMAIL = os.environ.get("TEST_USER_EMAIL", "")
TEST_PASSWORD = os.environ.get("TEST_USER_PASSWORD", "")


def login(page: Page) -> None:
    page.goto(f"{BASE_URL}/login")
    page.get_by_label("Email").fill(TEST_EMAIL)
    page.get_by_label("Password").fill(TEST_PASSWORD)
    page.get_by_role("button", name="Sign in").click()
    page.wait_for_url(f"{BASE_URL}/", timeout=10_000)


@pytest.mark.skipif(not TEST_EMAIL, reason="TEST_USER_EMAIL not set")
def test_query_bar_submit_navigates_to_meetings(page: Page) -> None:
    """Typing a query and pressing Enter navigates to /meetings?q=<query>."""
    login(page)
    query_input = page.get_by_placeholder("Ask Zabt anything about your meetings")
    query_input.fill("What were my last meeting action items?")
    query_input.press("Enter")
    page.wait_for_url(f"{BASE_URL}/meetings*", timeout=5_000)
    assert "q=" in page.url, f"Expected ?q= param in URL, got: {page.url}"


@pytest.mark.skipif(not TEST_EMAIL, reason="TEST_USER_EMAIL not set")
def test_empty_query_does_not_navigate(page: Page) -> None:
    """Clicking submit with an empty query does not navigate."""
    login(page)
    submit_button = page.get_by_role("button", name="Submit")
    # Submit button should be disabled
    expect(submit_button).to_be_disabled()
    # URL stays on home
    assert page.url.rstrip("/") == BASE_URL.rstrip("/"), (
        f"Unexpected navigation from home page, URL: {page.url}"
    )


@pytest.mark.skipif(not TEST_EMAIL, reason="TEST_USER_EMAIL not set")
def test_advanced_toggle(page: Page) -> None:
    """Clicking the Advanced toggle changes its appearance."""
    login(page)
    advanced_btn = page.get_by_role("button", name="Advanced")
    # Initially not active
    initial_classes = advanced_btn.get_attribute("class") or ""
    assert "indigo" not in initial_classes

    advanced_btn.click()
    active_classes = advanced_btn.get_attribute("class") or ""
    assert "indigo" in active_classes, "Advanced button should show active indigo style when toggled"
