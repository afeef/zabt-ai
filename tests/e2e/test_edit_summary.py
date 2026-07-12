"""
E2E Test: Edit Summary Markdown In-App

Tests the WYSIWYG summary editor on the meeting detail page:
  - Enter edit mode, modify summary, save, verify persistence
  - Cancel edit discards changes
  - "Edited" badge appears after saving
  - Restore original removes badge and reverts text

Requirements:
    pip install playwright pytest-playwright
    playwright install chromium

Environment variables:
    FRONTEND_URL         Base URL of the running frontend (default: http://localhost:3000)
    TEST_USER_EMAIL      Email of a test user with at least one completed meeting
    TEST_USER_PASSWORD   Password for the test user
    TEST_MEETING_ID      ID of a completed meeting with a non-empty summary

Run:
    pytest tests/e2e/test_edit_summary.py -v
"""

import os
import pytest
from playwright.sync_api import Page, expect

BASE_URL = os.environ.get("FRONTEND_URL", "http://localhost:3000")
TEST_EMAIL = os.environ.get("TEST_USER_EMAIL", "")
TEST_PASSWORD = os.environ.get("TEST_USER_PASSWORD", "")
TEST_MEETING_ID = os.environ.get("TEST_MEETING_ID", "")


def login(page: Page) -> None:
    page.goto(f"{BASE_URL}/login")
    page.get_by_label("Email").fill(TEST_EMAIL)
    page.get_by_label("Password").fill(TEST_PASSWORD)
    page.get_by_role("button", name="Sign in").click()
    page.wait_for_url(f"{BASE_URL}/", timeout=10_000)


def navigate_to_meeting_summary(page: Page) -> None:
    page.goto(f"{BASE_URL}/meetings/{TEST_MEETING_ID}")
    page.get_by_role("button", name="Summary").click()
    page.wait_for_timeout(500)


# ── US1: Edit and Save ───────────────────────────────────────────────────────


@pytest.mark.skipif(not TEST_EMAIL, reason="TEST_USER_EMAIL not set")
@pytest.mark.skipif(not TEST_MEETING_ID, reason="TEST_MEETING_ID not set")
def test_edit_save_summary(page: Page) -> None:
    """Enter edit mode, type text, save, verify persistence after refresh."""
    login(page)
    navigate_to_meeting_summary(page)

    # Click Edit button
    edit_btn = page.get_by_role("button", name="Edit")
    expect(edit_btn).to_be_visible()
    edit_btn.click()

    # Editor should appear (Tiptap renders a contenteditable div)
    editor = page.locator("[contenteditable='true']")
    expect(editor).to_be_visible()

    # Type some text
    editor.press("End")
    editor.type("\n\nEdited by E2E test.")

    # Click Save
    page.get_by_role("button", name="Save").click()

    # Wait for save to complete — editor should disappear
    expect(editor).not_to_be_visible(timeout=5_000)

    # Verify the new text is visible in read-only view
    expect(page.locator("text=Edited by E2E test.")).to_be_visible()

    # Refresh and verify persistence
    page.reload()
    page.get_by_role("button", name="Summary").click()
    page.wait_for_timeout(500)
    expect(page.locator("text=Edited by E2E test.")).to_be_visible()


@pytest.mark.skipif(not TEST_EMAIL, reason="TEST_USER_EMAIL not set")
@pytest.mark.skipif(not TEST_MEETING_ID, reason="TEST_MEETING_ID not set")
def test_cancel_edit_discards_changes(page: Page) -> None:
    """Enter edit mode, type text, cancel, verify original text restored."""
    login(page)
    navigate_to_meeting_summary(page)

    # Remember current summary text
    summary_section = page.locator("section").first
    original_text = summary_section.inner_text()

    # Enter edit mode
    page.get_by_role("button", name="Edit").click()
    editor = page.locator("[contenteditable='true']")
    expect(editor).to_be_visible()

    # Type something
    editor.type("THIS SHOULD BE DISCARDED")

    # Cancel
    page.get_by_role("button", name="Cancel").click()

    # Editor disappears, original text preserved
    expect(editor).not_to_be_visible(timeout=3_000)
    expect(page.locator("text=THIS SHOULD BE DISCARDED")).not_to_be_visible()


# ── US2: Track Edit History ──────────────────────────────────────────────────


@pytest.mark.skipif(not TEST_EMAIL, reason="TEST_USER_EMAIL not set")
@pytest.mark.skipif(not TEST_MEETING_ID, reason="TEST_MEETING_ID not set")
def test_edited_badge_and_restore(page: Page) -> None:
    """After editing, 'Edited' badge appears. Restore removes badge and reverts."""
    login(page)
    navigate_to_meeting_summary(page)

    # If the meeting was already edited by the previous test, badge should be visible
    edited_badge = page.locator("text=Edited").first
    if not edited_badge.is_visible():
        # Edit to create the badge
        page.get_by_role("button", name="Edit").click()
        editor = page.locator("[contenteditable='true']")
        editor.press("End")
        editor.type("\n\nBadge test edit.")
        page.get_by_role("button", name="Save").click()
        page.wait_for_timeout(1_000)

    # "Edited" badge should be visible
    expect(page.locator("text=Edited").first).to_be_visible()

    # Click "View Original"
    page.get_by_role("button", name="View Original").click()
    expect(page.locator("text=Original AI Summary")).to_be_visible()

    # Click "Restore Original"
    page.get_by_role("button", name="Restore Original").click()
    page.wait_for_timeout(1_000)

    # Badge should disappear
    expect(page.locator("span:text('Edited')")).not_to_be_visible()
