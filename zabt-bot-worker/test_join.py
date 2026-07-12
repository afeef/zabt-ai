"""Quick local test — launches browser and tries to join a Teams meeting.
No Docker, no S3, no backend. Just Playwright + the join flow.

Usage:
    cd zabt-bot-worker
    uv run python test_join.py "https://teams.live.com/meet/..."
"""

import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.dirname(__file__))

from src.browser import launch_browser, join_teams_meeting


async def main():
    if len(sys.argv) < 2:
        print("Usage: python test_join.py <teams-meeting-url>")
        sys.exit(1)

    join_url = sys.argv[1]
    display_name = "Zabt AI Notetaker"
    job_id = "local-test"

    # Use the current display (not Xvfb) for visual debugging
    env = os.environ.copy()
    # If DISPLAY is not set (headless server), you'll need Xvfb
    if "DISPLAY" not in env:
        print("No DISPLAY set — starting Xvfb...")
        import subprocess
        subprocess.Popen(
            ["Xvfb", ":99", "-screen", "0", "1280x720x24", "-ac"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        env["DISPLAY"] = ":99"
        await asyncio.sleep(1)

    print(f"Launching browser...")
    pw, browser = await launch_browser(env)

    try:
        print(f"Joining meeting: {join_url[:60]}...")
        page = await join_teams_meeting(browser, join_url, display_name, job_id)
        print("\n✅ JOIN FLOW COMPLETED")
        print("Screenshots saved to /tmp/bot_local-test_*.png")
        print("\nWaiting 30s so you can inspect screenshots...")
        await asyncio.sleep(30)
    except Exception as e:
        print(f"\n❌ JOIN FAILED: {e}")
        print("Check screenshots at /tmp/bot_local-test_*.png")
    finally:
        await browser.close()
        await pw.stop()


if __name__ == "__main__":
    asyncio.run(main())
