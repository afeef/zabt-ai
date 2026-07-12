# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2025-2026 Afeef Janjua
"""
E2E Test: Transcription Progress Tracking

Tests that processing stages are displayed in the upload modal, meetings list,
and meeting detail page with live polling updates.

Requirements:
    pip install playwright pytest-playwright
    playwright install chromium

Run:
    pytest tests/e2e/test_transcription_progress.py -v
"""

import os
import json
from playwright.sync_api import Page, Route, expect

BASE_URL = os.environ.get("FRONTEND_URL", "http://localhost:3000")
TEST_EMAIL = os.environ.get("TEST_USER_EMAIL", "")
TEST_PASSWORD = os.environ.get("TEST_USER_PASSWORD", "")


def login(page: Page) -> None:
    page.goto(f"{BASE_URL}/login")
    page.get_by_label("Email").fill(TEST_EMAIL)
    page.get_by_label("Password").fill(TEST_PASSWORD)
    page.get_by_role("button", name="Sign in").click()
    page.wait_for_url(f"{BASE_URL}/", timeout=10_000)


def make_meeting(
    id: int = 1,
    status: str = "processing",
    sub_status: str | None = "transcribing",
) -> dict:
    return {
        "id": id,
        "title": "test_recording.mp3",
        "description": None,
        "file_path": "user-uuid/test_recording.mp3",
        "duration_seconds": 120,
        "created_at": "2026-03-03T15:00:00",
        "status": status,
        "sub_status": sub_status,
        "transcript_text": None,
        "summary_text": None,
        "action_items_text": None,
        "segments": [],
        "speakers": None,
    }


def test_upload_modal_shows_stage_labels(page: Page) -> None:
    """Upload a file, keep modal open, verify stage labels appear during processing."""
    login(page)

    call_count = {"n": 0}

    def handle_presigned(route: Route) -> None:
        route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps({"upload_url": "http://localhost:9000/fake", "file_key": "user/test.mp3"}),
        )

    def handle_create_meeting(route: Route) -> None:
        route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(make_meeting(id=42, status="queued", sub_status=None)),
        )

    def handle_upload_to_minio(route: Route) -> None:
        route.fulfill(status=200, body="")

    def handle_get_meeting(route: Route) -> None:
        call_count["n"] += 1
        n = call_count["n"]
        if n == 1:
            meeting = make_meeting(id=42, status="processing", sub_status="transcribing")
        elif n == 2:
            meeting = make_meeting(id=42, status="processing", sub_status="aligning")
        elif n == 3:
            meeting = make_meeting(id=42, status="processing", sub_status="diarizing")
        else:
            meeting = make_meeting(id=42, status="completed", sub_status=None)
        route.fulfill(status=200, content_type="application/json", body=json.dumps(meeting))

    page.route("**/api/v1/meetings/presigned-upload", handle_presigned)
    page.route("**/api/v1/meetings/", handle_create_meeting)
    page.route("http://localhost:9000/**", handle_upload_to_minio)
    page.route("**/api/v1/meetings/42", handle_get_meeting)

    # Open upload modal
    page.get_by_role("button", name="Upload a meeting").first.click()
    expect(page.get_by_text("Transcribe audio and video")).to_be_visible()

    # Upload a file
    with page.expect_file_chooser() as fc_info:
        page.get_by_text("Browse files").click()
    fc_info.value.set_files("tests/e2e/test_transcription_progress.py")

    # Should eventually show a processing stage label (polling kicks in)
    expect(page.get_by_text("Transcribing")).to_be_visible(timeout=10_000)


def test_meetings_list_shows_stage_label(page: Page) -> None:
    """Navigate to meetings list while a meeting is processing, verify stage label."""
    login(page)

    def handle_meetings_list(route: Route) -> None:
        meetings = [make_meeting(id=1, status="processing", sub_status="aligning")]
        route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(meetings),
        )

    page.route("**/api/v1/meetings/?*", handle_meetings_list)
    page.route("**/api/v1/meetings/", handle_meetings_list)

    page.goto(f"{BASE_URL}/meetings")

    # The StatusBadge should show the specific stage label
    expect(page.get_by_text("Aligning")).to_be_visible(timeout=10_000)


def test_meeting_detail_shows_progress_steps(page: Page) -> None:
    """Open a processing meeting detail page, verify ProgressSteps indicator appears."""
    login(page)

    def handle_get_meeting(route: Route) -> None:
        meeting = make_meeting(id=5, status="processing", sub_status="diarizing")
        route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(meeting),
        )

    page.route("**/api/v1/meetings/5", handle_get_meeting)

    page.goto(f"{BASE_URL}/meetings/5")

    # Should show the specific stage label in the processing banner
    expect(page.get_by_text("Diarizing")).to_be_visible(timeout=10_000)

    # Should show the ProgressSteps indicator (check for step labels)
    expect(page.get_by_text("Uploaded")).to_be_visible()
    expect(page.get_by_text("Transcribing")).to_be_visible()


def test_meeting_detail_shows_completed_after_processing(page: Page) -> None:
    """Verify the detail page updates to completed state after polling."""
    login(page)

    call_count = {"n": 0}

    def handle_get_meeting(route: Route) -> None:
        call_count["n"] += 1
        if call_count["n"] <= 2:
            meeting = make_meeting(id=10, status="processing", sub_status="summarizing")
        else:
            meeting = make_meeting(id=10, status="completed", sub_status=None)
            meeting["summary_text"] = "This is the meeting summary."
        route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(meeting),
        )

    page.route("**/api/v1/meetings/10", handle_get_meeting)

    page.goto(f"{BASE_URL}/meetings/10")

    # Should eventually show Completed status
    expect(page.get_by_text("Completed")).to_be_visible(timeout=20_000)
