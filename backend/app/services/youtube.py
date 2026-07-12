# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2025-2026 Afeef Janjua
"""YouTube URL validation, metadata extraction, and audio download utilities.

Uses yt-dlp CLI via subprocess (stable interface per research decision #2).
"""

import json
import re
import subprocess
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# YouTube URL patterns (research decision #4)
_YOUTUBE_VIDEO_RE = re.compile(
    r"(?:https?://)?(?:www\.|m\.)?"
    r"(?:"
    r"youtube\.com/(?:watch\?.*v=|live/|shorts/|embed/)"
    r"|youtu\.be/"
    r")"
    r"[\w-]{11}"
)

_YOUTUBE_PLAYLIST_RE = re.compile(
    r"(?:https?://)?(?:www\.|m\.)?youtube\.com/playlist\?list="
)


class YouTubeError(Exception):
    """Base exception for YouTube-related errors."""

    pass


class VideoUnavailableError(YouTubeError):
    pass


class AgeRestrictedError(YouTubeError):
    pass


class LiveStreamError(YouTubeError):
    pass


class DurationExceededError(YouTubeError):
    pass


class NoAudioError(YouTubeError):
    pass


class DownloadError(YouTubeError):
    pass


def validate_youtube_url(url: str) -> bool:
    """Check if URL matches a known YouTube video URL pattern."""
    return bool(_YOUTUBE_VIDEO_RE.search(url))


def is_playlist_url(url: str) -> bool:
    """Check if URL is a YouTube playlist URL."""
    return bool(_YOUTUBE_PLAYLIST_RE.search(url))


def extract_metadata(url: str) -> dict:
    """Extract video metadata without downloading.

    Returns dict with keys: title, duration, thumbnail, channel, id.
    Raises YouTubeError subclasses for known failure modes.
    """
    try:
        result = subprocess.run(
            [
                "yt-dlp",
                "--dump-json",
                "--no-download",
                "--extractor-args",
                "youtube:player-client=android,web",
                url,
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )
    except subprocess.TimeoutExpired:
        raise YouTubeError("Timed out while fetching video information.")

    if result.returncode != 0:
        stderr = result.stderr.lower()
        _raise_for_stderr(stderr)
        
        logger.error(f"yt-dlp extraction failed: {result.stderr.strip()}")
        raise YouTubeError(
            f"Failed to fetch video metadata. Please check the URL and try again. Details: {result.stderr.strip()}"
        )

    data = json.loads(result.stdout)

    if data.get("is_live"):
        raise LiveStreamError(
            "Live streams in progress cannot be processed. "
            "Please wait until the stream ends."
        )

    return {
        "id": data.get("id", ""),
        "title": data.get("title", "YouTube Video"),
        "duration": int(data.get("duration", 0)),
        "thumbnail": data.get("thumbnail", ""),
        "channel": data.get("channel", data.get("uploader", "")),
    }


def download_audio(url: str, output_dir: str, video_id: str) -> str:
    """Download audio from YouTube video as MP3.

    Returns the path to the downloaded audio file.
    Raises YouTubeError subclasses for known failure modes.
    """
    output_template = str(Path(output_dir) / f"yt_{video_id}.%(ext)s")

    try:
        result = subprocess.run(
            [
                "yt-dlp",
                "-x",
                "--audio-format",
                "mp3",
                "--audio-quality",
                "0",
                "-o",
                output_template,
                "--no-playlist",
                "--extractor-args",
                "youtube:player-client=android,web",
                url,
            ],
            capture_output=True,
            text=True,
            timeout=1800,  # 30 min timeout for long videos
        )
    except subprocess.TimeoutExpired:
        raise DownloadError("Download timed out. The video may be too long.")

    if result.returncode != 0:
        stderr = result.stderr.lower()
        _raise_for_stderr(stderr)
        raise DownloadError("Failed to download audio. Please try again.")

    # Find the downloaded file (yt-dlp may adjust extension)
    output_path = Path(output_dir) / f"yt_{video_id}.mp3"
    if not output_path.exists():
        # Try to find any file matching the pattern
        candidates = list(Path(output_dir).glob(f"yt_{video_id}.*"))
        if candidates:
            output_path = candidates[0]
        else:
            raise DownloadError("Downloaded audio file not found.")

    logger.info("Downloaded YouTube audio to %s", output_path)
    return str(output_path)


def _raise_for_stderr(stderr: str) -> None:
    """Map yt-dlp stderr patterns to specific exceptions."""
    if "video unavailable" in stderr or "private video" in stderr:
        raise VideoUnavailableError(
            "Video unavailable \u2014 it may be private, deleted, or restricted."
        )
    if "age" in stderr and "restrict" in stderr:
        raise AgeRestrictedError(
            "Video is age-restricted and cannot be processed."
        )
    if "geo" in stderr and "block" in stderr:
        raise VideoUnavailableError(
            "Video unavailable \u2014 it may be private, deleted, or restricted."
        )
    if "no video formats" in stderr or "no audio" in stderr:
        raise NoAudioError("No audio track found in video.")
    if "is live" in stderr or "live event" in stderr:
        raise LiveStreamError(
            "Live streams in progress cannot be processed. "
            "Please wait until the stream ends."
        )
