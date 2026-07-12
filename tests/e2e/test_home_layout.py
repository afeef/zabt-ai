# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2025-2026 Afeef Janjua
"""
E2E Test: Home Layout — Three-Column Shell

Tests that a logged-in user sees the correct three-column authenticated shell
on the home page, including the Zabt AI logo, active Home nav link, and right panel.

Requirements:
    pip install playwright pytest-playwright
    playwright install chromium

Run:
    pytest tests/e2e/test_home_layout.py -v
"""

import os
import pytest
from playwright.sync_api import Page, expect

BASE_URL = os.environ.get("FRONTEND_URL", "http://localhost:3000")
TEST_EMAIL = os.environ.get("TEST_USER_EMAIL", "")
TEST_PASSWORD = os.environ.get("TEST_USER_PASSWORD", "")


def login(page: Page) -> None:
    """Helper: log in with test credentials."""
    page.goto(f"{BASE_URL}/login")
    page.get_by_label("Email").fill(TEST_EMAIL)
    page.get_by_label("Password").fill(TEST_PASSWORD)
    page.get_by_role("button", name="Sign in").click()
    page.wait_for_url(f"{BASE_URL}/", timeout=10_000)


@pytest.mark.skipif(not TEST_EMAIL, reason="TEST_USER_EMAIL not set")
def test_three_column_shell_renders(page: Page) -> None:
    """Three-column layout (sidebar + main + right panel) is visible after login."""
    login(page)

    # Sidebar: logo
    expect(page.get_by_text("Zabt AI")).to_be_visible()

    # Sidebar: active Home link
    home_link = page.get_by_role("link", name="Home")
    expect(home_link).to_be_visible()

    # AI query bar
    expect(page.get_by_placeholder("Ask Zabt anything about your meetings")).to_be_visible()

    # Right panel: quick action
    expect(page.get_by_role("link", name="Upload a meeting")).to_be_visible()


@pytest.mark.skipif(not TEST_EMAIL, reason="TEST_USER_EMAIL not set")
def test_no_horizontal_scroll(page: Page) -> None:
    """Home page must not have horizontal overflow."""
    login(page)
    scroll_width = page.evaluate("document.body.scrollWidth")
    client_width = page.evaluate("document.body.clientWidth")
    assert scroll_width <= client_width, (
        f"Horizontal scroll detected: scrollWidth={scroll_width}, clientWidth={client_width}"
    )


@pytest.mark.skipif(not TEST_EMAIL, reason="TEST_USER_EMAIL not set")
def test_sidebar_nav_link_active_highlight(page: Page) -> None:
    """Home nav link has active styling (indigo background) when on the home page."""
    login(page)
    home_link = page.get_by_role("link", name="Home")
    # Active link has bg-indigo-50 class applied
    link_classes = home_link.get_attribute("class") or ""
    assert "indigo" in link_classes, (
        f"Expected active indigo style on Home link, got classes: {link_classes}"
    )


@pytest.mark.skipif(not TEST_EMAIL, reason="TEST_USER_EMAIL not set")
def test_unauthenticated_redirects_to_login(page: Page) -> None:
    """Visiting / without a session redirects to /login."""
    page.goto(BASE_URL)
    page.wait_for_url(f"{BASE_URL}/login", timeout=8_000)
    expect(page.get_by_role("heading", name="Sign in")).to_be_visible()
