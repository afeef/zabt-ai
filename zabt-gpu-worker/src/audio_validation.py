# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2025-2026 Afeef Janjua
"""Audio file validation — ensures files contain an audio stream before processing."""

import json
import subprocess

from src.logging import get_logger

logger = get_logger(__name__)


def validate_audio_stream(file_path: str) -> None:
    """Check that the file contains at least one audio stream using ffprobe.

    Raises ValueError with a user-friendly message if no audio stream is found.
    """
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "quiet",
                "-print_format", "json",
                "-show_streams",
                "-select_streams", "a",
                file_path,
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        probe = json.loads(result.stdout)
        streams = probe.get("streams", [])
    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError) as e:
        logger.warning("ffprobe failed for %s: %s — skipping validation", file_path, e)
        return

    if not streams:
        raise ValueError(
            "The uploaded file contains no audio stream. "
            "Please upload a file with audio (e.g., .mp3, .wav, .m4a, or a video with sound)."
        )

    logger.info("Audio validation passed: %d audio stream(s) found", len(streams))
