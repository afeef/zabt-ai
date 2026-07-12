# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2025-2026 Afeef Janjua
"""Audio recorder — captures audio from a PulseAudio monitor source via ffmpeg."""

import os
import signal
import subprocess

from src.logging import get_logger

logger = get_logger(__name__)


class AudioRecorder:
    """Records audio from a PulseAudio null-sink monitor to a WAV file."""

    def __init__(self, pulse_monitor: str, output_path: str):
        self.pulse_monitor = pulse_monitor  # e.g. "meeting_100.monitor"
        self.output_path = output_path
        self._process: subprocess.Popen | None = None

    def start(self) -> None:
        """Start ffmpeg recording from the PulseAudio monitor."""
        cmd = [
            "ffmpeg",
            "-y",  # overwrite output
            "-f", "pulse",
            "-i", self.pulse_monitor,
            "-ac", "1",           # mono
            "-ar", "16000",       # 16kHz sample rate
            "-acodec", "pcm_s16le",
            self.output_path,
        ]
        self._process = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        logger.info(
            "Recording started: monitor=%s output=%s pid=%d",
            self.pulse_monitor, self.output_path, self._process.pid,
        )

    def stop(self) -> float:
        """Stop recording and return duration in seconds."""
        if not self._process:
            return 0.0

        # Send SIGINT to ffmpeg for clean shutdown (writes proper WAV header)
        self._process.send_signal(signal.SIGINT)
        try:
            self._process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self._process.kill()
            self._process.wait()

        logger.info("Recording stopped: output=%s", self.output_path)

        # Calculate duration from file size
        if os.path.exists(self.output_path):
            file_size = os.path.getsize(self.output_path)
            # WAV header is 44 bytes, 16-bit mono 16kHz = 32000 bytes/sec
            data_size = max(0, file_size - 44)
            duration = data_size / 32000.0
            return duration
        return 0.0

    @property
    def is_recording(self) -> bool:
        return self._process is not None and self._process.poll() is None
