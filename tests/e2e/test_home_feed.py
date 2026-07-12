"""
E2E Test: Home Meeting Feed

Tests the home page meeting activity feed — both the empty state and
the happy path when meetings exist.

Requirements:
    pip install playwright pytest-playwright
    playwright install chromium

Run:
    pytest tests/e2e/test_home_feed.py -v
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
def test_empty_state_shows_upload_cta(page: Page) -> None:
    """When no meetings exist the feed shows the empty state and an upload CTA."""
    login(page)
    # Wait for feed to load (skeleton disappears)
    page.wait_for_timeout(1500)

    # If no meetings: empty-state text should be visible
    empty_heading = page.get_by_text("No meetings yet")
    if empty_heading.is_visible():
        expect(page.get_by_role("link", name="Upload a meeting")).to_be_visible()


@pytest.mark.skipif(not TEST_EMAIL, reason="TEST_USER_EMAIL not set")
def test_meeting_cards_show_when_meetings_exist(page: Page) -> None:
    """When meetings exist the feed shows at least one card with a title."""
    login(page)
    page.wait_for_timeout(1500)

    empty_heading = page.get_by_text("No meetings yet")
    if not empty_heading.is_visible():
        # At least one meeting card should be present
        cards = page.locator("a[href^='/meetings/']")
        assert cards.count() > 0, "Expected at least one meeting card in the feed"


@pytest.mark.skipif(not TEST_EMAIL, reason="TEST_USER_EMAIL not set")
def test_clicking_meeting_card_navigates_to_detail(page: Page) -> None:
    """Clicking a meeting card navigates to /meetings/[id]."""
    login(page)
    page.wait_for_timeout(1500)

    empty_heading = page.get_by_text("No meetings yet")
    if not empty_heading.is_visible():
        first_card = page.locator("a[href^='/meetings/']").first
        first_card.click()
        page.wait_for_url(f"{BASE_URL}/meetings/*", timeout=5_000)
        assert "/meetings/" in page.url, (
            f"Expected to be on a meeting detail page, got: {page.url}"
        )
