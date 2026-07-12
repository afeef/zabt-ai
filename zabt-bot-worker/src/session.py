"""Meeting session — manages Xvfb + PulseAudio + Chromium lifecycle per meeting."""

import os
import subprocess
import tempfile
from threading import Lock

from src.logging import get_logger
from src.recorder import AudioRecorder

logger = get_logger(__name__)

# Display number pool — recycles numbers on session teardown
_display_pool: set[int] = set()
_display_lock = Lock()
_DISPLAY_START = 100
_DISPLAY_MAX = 200


def _allocate_display() -> int:
    with _display_lock:
        for num in range(_DISPLAY_START, _DISPLAY_MAX):
            if num not in _display_pool:
                _display_pool.add(num)
                return num
    raise RuntimeError("No available display numbers")


def _release_display(num: int) -> None:
    with _display_lock:
        _display_pool.discard(num)


class MeetingSession:
    """One session per meeting — isolated display, audio sink, browser, recorder."""

    def __init__(self, job_id: str):
        self.job_id = job_id
        self.display_num = _allocate_display()
        self.pulse_sink = f"meeting_{self.display_num}"
        self.audio_path = os.path.join(tempfile.gettempdir(), f"meeting_{job_id}.wav")
        self._xvfb_proc: subprocess.Popen | None = None
        self._recorder: AudioRecorder | None = None
        self._sink_module_index: str | None = None

    def start(self) -> None:
        """Launch Xvfb display and create PulseAudio null-sink."""
        # Start Xvfb on the allocated display
        self._xvfb_proc = subprocess.Popen(
            ["Xvfb", f":{self.display_num}", "-screen", "0", "1280x720x24", "-ac"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        logger.info("Xvfb started display=:%d pid=%d", self.display_num, self._xvfb_proc.pid)

        # Create PulseAudio null-sink — capture the module index for targeted unload
        result = subprocess.run(
            [
                "pactl", "load-module", "module-null-sink",
                f"sink_name={self.pulse_sink}",
                f"sink_properties=device.description={self.pulse_sink}",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        self._sink_module_index = result.stdout.strip()
        logger.info("PulseAudio sink created: %s (module index: %s)", self.pulse_sink, self._sink_module_index)

    @property
    def display_env(self) -> dict:
        """Environment variables for launching Chromium on this session's display + audio sink."""
        env = os.environ.copy()
        env["DISPLAY"] = f":{self.display_num}"
        env["PULSE_SINK"] = self.pulse_sink
        return env

    def start_recording(self) -> None:
        """Start ffmpeg recording from this session's PulseAudio monitor."""
        monitor = f"{self.pulse_sink}.monitor"
        self._recorder = AudioRecorder(monitor, self.audio_path)
        self._recorder.start()

    def stop_recording(self) -> float:
        """Stop recording and return duration in seconds."""
        if self._recorder:
            return self._recorder.stop()
        return 0.0

    def stop(self) -> None:
        """Tear down the entire session — recorder, Xvfb, PulseAudio sink."""
        # Stop recording
        if self._recorder and self._recorder.is_recording:
            self._recorder.stop()

        # Unload only THIS session's PulseAudio sink (by module index)
        if self._sink_module_index:
            try:
                subprocess.run(
                    ["pactl", "unload-module", self._sink_module_index],
                    capture_output=True,
                    timeout=5,
                )
                logger.info("PulseAudio sink unloaded: module index %s", self._sink_module_index)
            except Exception:
                logger.warning("Failed to unload PulseAudio sink module %s", self._sink_module_index)

        # Stop Xvfb
        if self._xvfb_proc:
            self._xvfb_proc.terminate()
            try:
                self._xvfb_proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._xvfb_proc.kill()
            logger.info("Xvfb stopped display=:%d", self.display_num)

        # Clean up Xvfb lock file so display number can be reused
        lock_file = f"/tmp/.X{self.display_num}-lock"
        if os.path.exists(lock_file):
            try:
                os.unlink(lock_file)
            except Exception:
                pass

        # Recycle display number
        _release_display(self.display_num)

        # Clean up audio file if empty
        if os.path.exists(self.audio_path) and os.path.getsize(self.audio_path) < 100:
            os.unlink(self.audio_path)
