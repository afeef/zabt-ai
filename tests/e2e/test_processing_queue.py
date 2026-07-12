"""
E2E Test: Unified Processing Queue

Tests the processing queue panel that appears after file uploads or YouTube
submissions, including stage progress, collapse/expand, auto-hide, navigation,
and error display.

Requirements:
    pip install playwright pytest-playwright
    playwright install chromium

Run:
    pytest tests/e2e/test_processing_queue.py -v
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
    title: str = "test_recording.mp3",
    status: str = "processing",
    sub_status: str | None = "transcribing",
    source_type: str = "upload",
    source_url: str | None = None,
    youtube_title: str | None = None,
) -> dict:
    return {
        "id": id,
        "title": title,
        "description": None,
        "file_path": f"user-uuid/{title}",
        "duration_seconds": 120,
        "created_at": "2026-03-10T14:00:00",
        "status": status,
        "sub_status": sub_status,
        "transcript_text": None,
        "summary_text": None,
        "original_summary_text": None,
        "summary_edited": False,
        "action_items_text": None,
        "template_id": None,
        "template_name": None,
        "source_type": source_type,
        "source_url": source_url,
        "youtube_title": youtube_title,
        "youtube_duration_seconds": None,
        "youtube_thumbnail_url": None,
        "youtube_channel": None,
        "segments": [],
        "speakers": None,
    }


def mock_meetings_list(page: Page, meetings: list[dict] | None = None) -> None:
    """Intercept the meetings list endpoint with an empty or provided list."""
    data = meetings or []

    def handler(route: Route) -> None:
        route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(data),
        )

    page.route("**/api/v1/meetings/?*", handler)
    page.route("**/api/v1/meetings/", handler)


def mock_upload_flow(page: Page, meeting_id: int = 42) -> None:
    """Intercept presigned-upload, meetings POST, and the PUT upload."""

    def handle_presigned(route: Route) -> None:
        route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps({
                "upload_url": "http://localhost:9000/fake-bucket/fake-key",
                "file_key": "user-uuid/test.mp3",
                "storage_provider": "minio",
            }),
        )

    def handle_create_meeting(route: Route) -> None:
        route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(make_meeting(
                id=meeting_id,
                status="queued",
                sub_status=None,
            )),
        )

    def handle_put_upload(route: Route) -> None:
        route.fulfill(status=200, body="")

    page.route("**/api/v1/meetings/presigned-upload", handle_presigned)
    page.route("**/api/v1/meetings/", handle_create_meeting)
    page.route("http://localhost:9000/**", handle_put_upload)


def trigger_file_upload(page: Page) -> None:
    """Open the upload modal and select a mock file."""
    page.get_by_role("button", name="Import").click()
    expect(page.get_by_text("Transcribe audio and video")).to_be_visible()

    with page.expect_file_chooser() as fc_info:
        page.get_by_text("Browse files").click()
    fc_info.value.set_files("tests/e2e/test_processing_queue.py")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_queue_appears_after_file_upload(page: Page) -> None:
    """Upload a file and verify the queue panel appears with the file name."""
    login(page)
    mock_meetings_list(page)

    meeting_id = 42

    mock_upload_flow(page, meeting_id=meeting_id)

    # Keep the queue item in processing state so panel stays visible
    def handle_get_meeting(route: Route) -> None:
        route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(make_meeting(
                id=meeting_id,
                status="processing",
                sub_status="transcribing",
            )),
        )

    page.route(f"**/api/v1/meetings/{meeting_id}", handle_get_meeting)

    trigger_file_upload(page)

    # Queue panel should appear with the "Processing" header
    expect(page.get_by_text("Processing")).to_be_visible(timeout=10_000)

    # The file name should be visible in the queue
    expect(page.get_by_text("test_processing_queue.py")).to_be_visible(timeout=5_000)


def test_queue_appears_after_youtube_submission(page: Page) -> None:
    """Submit a YouTube URL and verify the queue panel appears."""
    login(page)
    mock_meetings_list(page)

    meeting_id = 99
    yt_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

    def handle_youtube(route: Route) -> None:
        route.fulfill(
            status=201,
            content_type="application/json",
            body=json.dumps(make_meeting(
                id=meeting_id,
                title="YouTube Video",
                status="queued",
                sub_status=None,
                source_type="youtube",
                source_url=yt_url,
                youtube_title="Rick Astley - Never Gonna Give You Up",
            )),
        )

    def handle_get_meeting(route: Route) -> None:
        route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(make_meeting(
                id=meeting_id,
                status="processing",
                sub_status="downloading_youtube",
                source_type="youtube",
            )),
        )

    page.route("**/api/v1/meetings/youtube", handle_youtube)
    page.route(f"**/api/v1/meetings/{meeting_id}", handle_get_meeting)

    # Open the YouTube dialog via the link icon button
    page.locator("button").filter(has=page.locator("svg.lucide-link-2")).click()
    expect(page.get_by_text("Paste YouTube URL")).to_be_visible()

    page.get_by_placeholder("https://www.youtube.com/watch?v=").fill(yt_url)
    page.get_by_role("button", name="Process").click()

    # Dialog should close and queue panel should appear
    expect(page.get_by_text("Paste YouTube URL")).not_to_be_visible(timeout=5_000)
    expect(page.get_by_text("Processing")).to_be_visible(timeout=10_000)

    # The YouTube title should show as the display name
    expect(page.get_by_text("Rick Astley - Never Gonna Give You Up")).to_be_visible(timeout=5_000)


def test_queue_shows_stage_progress(page: Page) -> None:
    """Mock meeting GET to return changing processing status and verify stage labels update."""
    login(page)
    mock_meetings_list(page)

    meeting_id = 50
    mock_upload_flow(page, meeting_id=meeting_id)

    call_count = {"n": 0}

    def handle_get_meeting(route: Route) -> None:
        call_count["n"] += 1
        n = call_count["n"]
        if n <= 2:
            meeting = make_meeting(id=meeting_id, status="processing", sub_status="transcribing")
        elif n <= 4:
            meeting = make_meeting(id=meeting_id, status="processing", sub_status="diarizing")
        else:
            meeting = make_meeting(id=meeting_id, status="processing", sub_status="summarizing")
        route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(meeting),
        )

    page.route(f"**/api/v1/meetings/{meeting_id}", handle_get_meeting)

    trigger_file_upload(page)

    # Should see "Transcribing" stage label first
    expect(page.get_by_text("Transcribing")).to_be_visible(timeout=10_000)

    # Should eventually advance to "Diarizing"
    expect(page.get_by_text("Diarizing")).to_be_visible(timeout=15_000)

    # Then "Summarizing"
    expect(page.get_by_text("Summarizing")).to_be_visible(timeout=15_000)


def test_queue_auto_hides_after_completion(page: Page) -> None:
    """Mock meeting as completed and verify queue panel disappears after the auto-hide delay."""
    login(page)
    mock_meetings_list(page)

    meeting_id = 60
    mock_upload_flow(page, meeting_id=meeting_id)

    def handle_get_meeting(route: Route) -> None:
        meeting = make_meeting(id=meeting_id, status="completed", sub_status=None)
        route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(meeting),
        )

    page.route(f"**/api/v1/meetings/{meeting_id}", handle_get_meeting)

    trigger_file_upload(page)

    # Queue should appear
    expect(page.get_by_text("Processing")).to_be_visible(timeout=10_000)

    # Item should reach "Done" state
    expect(page.get_by_text("Done")).to_be_visible(timeout=10_000)

    # After auto-hide delay (10s), the panel should disappear
    # The "Processing" header is the queue panel marker
    processing_header = page.locator("h3").filter(has_text="Processing")
    expect(processing_header).not_to_be_visible(timeout=15_000)


def test_queue_collapse_expand(page: Page) -> None:
    """Click collapse button, verify compact pill, click expand, verify full panel returns."""
    login(page)
    mock_meetings_list(page)

    meeting_id = 70
    mock_upload_flow(page, meeting_id=meeting_id)

    def handle_get_meeting(route: Route) -> None:
        meeting = make_meeting(id=meeting_id, status="processing", sub_status="aligning")
        route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(meeting),
        )

    page.route(f"**/api/v1/meetings/{meeting_id}", handle_get_meeting)

    trigger_file_upload(page)

    # Wait for queue panel to appear (full expanded view has the "Processing" header)
    processing_header = page.locator("h3").filter(has_text="Processing")
    expect(processing_header).to_be_visible(timeout=10_000)

    # Click the collapse button (ChevronDown icon in header)
    page.locator("svg.lucide-chevron-down").click()

    # The full panel header should disappear
    expect(processing_header).not_to_be_visible()

    # The collapsed pill should show "processing" text
    expect(page.get_by_text("processing", exact=False)).to_be_visible(timeout=5_000)

    # Click the collapsed pill to expand (it has a ChevronUp icon)
    page.locator("svg.lucide-chevron-up").click()

    # Full panel should be back
    expect(processing_header).to_be_visible(timeout=5_000)


def test_completed_item_navigates_to_meeting(page: Page) -> None:
    """Mock a completed meeting item and verify clicking it navigates to /meetings/{id}."""
    login(page)
    mock_meetings_list(page)

    meeting_id = 80
    mock_upload_flow(page, meeting_id=meeting_id)

    def handle_get_meeting(route: Route) -> None:
        meeting = make_meeting(id=meeting_id, status="completed", sub_status=None)
        meeting["summary_text"] = "This is a summary."
        route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(meeting),
        )

    page.route(f"**/api/v1/meetings/{meeting_id}", handle_get_meeting)

    trigger_file_upload(page)

    # Wait for the item to show as Done
    expect(page.get_by_text("Done")).to_be_visible(timeout=10_000)

    # Click the completed queue item (it has the file name)
    page.get_by_text("test_processing_queue.py").click()

    # Should navigate to the meeting detail page
    page.wait_for_url(f"**/meetings/{meeting_id}", timeout=5_000)


def test_failed_item_shows_error(page: Page) -> None:
    """Mock a failed meeting and verify the error message displays in the queue."""
    login(page)
    mock_meetings_list(page)

    meeting_id = 90
    mock_upload_flow(page, meeting_id=meeting_id)

    error_message = "Audio extraction failed"

    def handle_get_meeting(route: Route) -> None:
        meeting = make_meeting(
            id=meeting_id,
            status="failed",
            sub_status=error_message,
        )
        route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(meeting),
        )

    page.route(f"**/api/v1/meetings/{meeting_id}", handle_get_meeting)

    trigger_file_upload(page)

    # Queue panel should appear
    expect(page.get_by_text("Processing")).to_be_visible(timeout=10_000)

    # The error message should be displayed in place of the stage label
    expect(page.get_by_text(error_message)).to_be_visible(timeout=10_000)
