"""Playwright automation — join Teams meetings via the web client.

Uses primary CSS selectors with text-based fallback heuristics
for resilience against Teams UI changes.
"""

import asyncio
import os
import tempfile

from playwright.async_api import Page, Browser, async_playwright, TimeoutError as PwTimeout

from src.config import settings
from src.logging import get_logger

logger = get_logger(__name__)

# Chrome flags for headful Chromium in Docker
CHROME_ARGS = [
    "--use-fake-ui-for-media-stream",       # auto-grant mic/camera permissions
    "--use-fake-device-for-media-stream",    # dummy mic/camera
    "--disable-gpu",
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-extensions",
    "--disable-background-timer-throttling",
    "--disable-backgrounding-occluded-windows",
    "--disable-renderer-backgrounding",
]


async def _click_with_fallback(
    page: Page, primary: str, fallback_text: str, timeout: int = 15000,
    alt_texts: list[str] | None = None,
) -> None:
    """Try CSS selector first, fall back to text-based locators."""
    try:
        await page.click(primary, timeout=timeout)
        logger.info("Clicked primary selector: %s", primary)
        return
    except PwTimeout:
        logger.info("Primary selector timed out: %s, trying text fallbacks", primary)

    # Try all text variations
    texts_to_try = [fallback_text] + (alt_texts or [])
    for text in texts_to_try:
        try:
            await page.get_by_text(text, exact=False).first.click(timeout=5000)
            logger.info("Clicked text fallback: %s", text)
            return
        except PwTimeout:
            continue

    # Last resort: try role-based with all text variations
    for text in texts_to_try:
        try:
            await page.get_by_role("button", name=text).first.click(timeout=5000)
            logger.info("Clicked role fallback: button[%s]", text)
            return
        except PwTimeout:
            continue

    all_tried = ", ".join(texts_to_try)
    raise RuntimeError(f"Could not find element: selector={primary}, texts=[{all_tried}]")


async def _take_screenshot(page: Page, step: str, job_id: str) -> str:
    """Save a debug screenshot and return the path."""
    path = os.path.join(tempfile.gettempdir(), f"bot_{job_id}_{step}.png")
    try:
        await page.screenshot(path=path)
        logger.info("Screenshot saved: %s", path)
    except Exception:
        logger.warning("Failed to take screenshot for step %s", step)
    return path


async def launch_browser(session_env: dict) -> tuple:
    """Launch Playwright Chromium with the session's display + audio env. Returns (playwright, browser)."""
    logger.info("launch_browser: DISPLAY=%s", session_env.get("DISPLAY"))
    
    pw = await async_playwright().start()
    browser = await pw.chromium.launch(
        headless=False,  # Must be headful for WebRTC audio
        args=CHROME_ARGS,
        env=session_env,
    )
    display = session_env.get("DISPLAY", "?")
    sink = session_env.get("PULSE_SINK", "?")
    logger.info("Browser launched on display=%s sink=%s", display, sink)
    return pw, browser


async def join_teams_meeting(
    browser: Browser, join_url: str, display_name: str, job_id: str
) -> Page:
    """Navigate through the Teams web client join flow. Returns the meeting page."""
    logger.info("join_teams_meeting: job_id=%s display_name=%s url_preview=%.50s", 
                job_id, display_name, join_url[:50])
    
    page = await browser.new_page()
    await page.set_viewport_size({"width": 1280, "height": 720})

    # Step 1: Navigate to join URL and wait for the page to fully load
    logger.info("Navigating to Teams meeting URL")
    await page.goto(join_url, wait_until="networkidle", timeout=60000)
    await _take_screenshot(page, "01_landing", job_id)

    # Wait for the join page to appear (past the Teams splash/loading screen)
    # Teams shows different text depending on version: "Continue on this browser",
    # "Join on the web", "Use the web app instead", etc.
    logger.info("Waiting for Teams join page to load...")
    join_page_loaded = False
    for wait_text in ["Continue on this browser", "Join on the web", "Use the web app", "join", "Join"]:
        try:
            await page.get_by_text(wait_text, exact=False).first.wait_for(state="visible", timeout=10000)
            join_page_loaded = True
            logger.info("Join page loaded — found text: '%s'", wait_text)
            break
        except PwTimeout:
            continue

    if not join_page_loaded:
        # Last resort: wait longer and take screenshot for debugging
        logger.warning("Join page text not found after initial wait, waiting 15s more...")
        await asyncio.sleep(15)
        await _take_screenshot(page, "01b_extended_wait", job_id)

    await _take_screenshot(page, "02_before_continue", job_id)

    # Step 2: Click "Continue on this browser" — OPTIONAL
    # Teams sometimes skips this and goes straight to the pre-join screen
    # (name input + "Join now" button). Detect which page we're on.
    already_on_prejoin = False
    try:
        # Check if name input or "Join now" is already visible (= pre-join screen)
        for indicator in ["Type your name", "Join now", "Enter your name"]:
            if await page.get_by_text(indicator, exact=False).first.is_visible():
                already_on_prejoin = True
                logger.info("Already on pre-join screen (found '%s'), skipping 'Continue on this browser'", indicator)
                break
    except Exception:
        pass

    if not already_on_prejoin:
        logger.info("Looking for join-on-web button")
        try:
            await _click_with_fallback(
                page,
                primary="[data-tid='joinOnWeb']",
                fallback_text="Continue on this browser",
                alt_texts=["Join on the web", "Use the web app instead", "Use the web app"],
                timeout=15000,
            )
            await asyncio.sleep(3)
        except RuntimeError:
            logger.warning("Could not find join-on-web button — may already be on pre-join screen")

    await _take_screenshot(page, "03_prejoin", job_id)

    # Step 3: Enter display name
    logger.info("Entering display name: %s", display_name)
    name_filled = False
    for selector in [
        "input[placeholder='Type your name']",
        "input[data-tid='prejoin-display-name']",
        "input[placeholder*='name' i]",
        "input[aria-label*='name' i]",
    ]:
        try:
            await page.fill(selector, display_name, timeout=5000)
            name_filled = True
            logger.info("Name filled via selector: %s", selector)
            break
        except PwTimeout:
            continue

    if not name_filled:
        # Try finding any visible text input
        try:
            inputs = page.locator("input[type='text']:visible")
            if await inputs.count() > 0:
                await inputs.first.fill(display_name, timeout=5000)
                name_filled = True
                logger.info("Name filled via generic text input")
        except PwTimeout:
            pass

    if not name_filled:
        logger.warning("Could not find name input — proceeding anyway")

    await _take_screenshot(page, "04_name_entered", job_id)

    # Step 4a: Turn off camera (defaults to ON with fake device)
    for camera_selector in ["[data-tid='toggle-video']", "[aria-label*='camera' i]", "[aria-label*='video' i]"]:
        try:
            await page.click(camera_selector, timeout=3000)
            logger.info("Camera toggled off via: %s", camera_selector)
            break
        except PwTimeout:
            continue

    # Step 4b: Turn off microphone (fake device generates ticking noise)
    # Strategy: find the mic toggle, check if it's currently ON (aria-pressed/aria-checked),
    # and only click if it needs to be turned OFF.
    mic_muted = False
    for mic_selector in ["[data-tid='toggle-audio']", "[aria-label*='microphone' i]", "[aria-label*='mic' i]", "[aria-label*='Mute' i]"]:
        try:
            el = page.locator(mic_selector).first
            await el.wait_for(state="visible", timeout=3000)
            # Check if mic is currently unmuted (aria-label usually says "Mute" when active)
            label = await el.get_attribute("aria-label") or ""
            if "unmute" in label.lower() or "turn on" in label.lower():
                logger.info("Mic already muted (label=%s)", label)
                mic_muted = True
            else:
                await el.click()
                logger.info("Mic toggled off via: %s (label was: %s)", mic_selector, label)
                mic_muted = True
            break
        except PwTimeout:
            continue

    if not mic_muted:
        # Fallback: use keyboard shortcut Ctrl+Shift+M (Teams mute shortcut)
        try:
            await page.keyboard.press("Control+Shift+m")
            logger.info("Mic muted via keyboard shortcut Ctrl+Shift+M")
            mic_muted = True
        except Exception:
            logger.warning("Failed to mute mic via keyboard shortcut")

    if not mic_muted:
        logger.warning("Could not mute mic — meeting may have background noise")

    await _take_screenshot(page, "04b_av_off", job_id)

    # Step 5: Click "Join now"
    logger.info("Clicking 'Join now'")
    await _click_with_fallback(
        page,
        primary="[data-tid='prejoin-join-button']",
        fallback_text="Join now",
        timeout=15000,
    )
    await _take_screenshot(page, "05_join_clicked", job_id)
    await asyncio.sleep(5)

    # Post-join safety mute — Teams sometimes resets mic state on join
    try:
        await page.keyboard.press("Control+Shift+m")
        logger.info("Post-join mute applied via Ctrl+Shift+M")
    except Exception:
        logger.warning("Post-join mute shortcut failed")

    await _take_screenshot(page, "06_after_join", job_id)

    logger.info("Join flow completed for job %s", job_id)
    return page


async def detect_meeting_state(page: Page) -> str:
    """Check the current meeting state. Returns 'in_meeting', 'lobby', or 'ended'.

    Uses targeted Playwright locator checks instead of full-page content parsing.
    """
    try:
        # Check for meeting ended indicators
        for phrase in ["meeting has ended", "You left the meeting", "Rejoin"]:
            if await page.get_by_text(phrase, exact=False).first.is_visible():
                return "ended"

        # Check for lobby
        for phrase in ["waiting for someone to let you in", "lobby", "let you in soon"]:
            if await page.get_by_text(phrase, exact=False).first.is_visible():
                return "lobby"

        return "in_meeting"

    except Exception:
        logger.warning("Failed to detect meeting state")
        return "in_meeting"


async def wait_for_meeting_end(
    page: Page, job_id: str, max_duration_hours: int = 4, lobby_timeout_seconds: int = 300
) -> str:
    """Poll until the meeting ends, lobby timeout, or max duration. Returns final state."""
    max_seconds = max_duration_hours * 3600
    elapsed = 0
    lobby_elapsed = 0
    poll_interval = 5

    while elapsed < max_seconds:
        state = await detect_meeting_state(page)

        if state == "ended":
            logger.info("Meeting ended for job %s after %ds", job_id, elapsed)
            return "ended"

        if state == "lobby":
            lobby_elapsed += poll_interval
            if lobby_elapsed > lobby_timeout_seconds:
                logger.warning("Lobby timeout for job %s after %ds", job_id, lobby_elapsed)
                return "lobby_timeout"
        else:
            lobby_elapsed = 0  # Reset if admitted

        await asyncio.sleep(poll_interval)
        elapsed += poll_interval

        # Log state every 60 seconds
        if elapsed % 60 == 0:
            logger.info("Meeting ongoing job=%s elapsed=%ds state=%s", job_id, elapsed, state)

    logger.warning("Meeting timed out for job %s after %ds", job_id, max_seconds)
    return "timeout"
