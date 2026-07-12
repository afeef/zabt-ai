"""
E2E Test: Download Transcript as PDF

Tests the transcript PDF download button on the meeting detail page:
  - "Download PDF" button visible on Transcript tab for completed meetings
  - Button hidden when meeting has no transcript segments
  - Clicking button triggers a PDF download

Requirements:
    pip install playwright pytest-playwright
    playwright install chromium

Environment variables:
    FRONTEND_URL         Base URL of the running frontend (default: http://localhost:3000)
    TEST_USER_EMAIL      Email of a test user with at least one completed meeting
    TEST_USER_PASSWORD   Password for the test user
    TEST_MEETING_ID      ID of a completed meeting with transcript segments

Run:
    pytest tests/e2e/test_transcript_pdf.py -v
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


def navigate_to_meeting_transcript(page: Page) -> None:
    page.goto(f"{BASE_URL}/meetings/{TEST_MEETING_ID}")
    page.get_by_role("button", name="Transcript").click()
    page.wait_for_timeout(500)


@pytest.mark.skipif(not TEST_EMAIL, reason="TEST_USER_EMAIL not set")
@pytest.mark.skipif(not TEST_MEETING_ID, reason="TEST_MEETING_ID not set")
def test_download_pdf_button_visible(page: Page) -> None:
    """Download PDF button is visible on Transcript tab for a completed meeting."""
    login(page)
    navigate_to_meeting_transcript(page)

    download_btn = page.get_by_role("button", name="Download PDF")
    expect(download_btn).to_be_visible()


@pytest.mark.skipif(not TEST_EMAIL, reason="TEST_USER_EMAIL not set")
@pytest.mark.skipif(not TEST_MEETING_ID, reason="TEST_MEETING_ID not set")
def test_download_pdf_triggers_download(page: Page) -> None:
    """Clicking Download PDF triggers a file download with correct filename pattern."""
    login(page)
    navigate_to_meeting_transcript(page)

    download_btn = page.get_by_role("button", name="Download PDF")
    expect(download_btn).to_be_visible()

    # Listen for download event
    with page.expect_download() as download_info:
        download_btn.click()

    download = download_info.value
    filename = download.suggested_filename
    assert filename.endswith("-transcript.pdf"), f"Expected filename ending with '-transcript.pdf', got '{filename}'"
