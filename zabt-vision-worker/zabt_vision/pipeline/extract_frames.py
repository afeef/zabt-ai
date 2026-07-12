import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Frame:
    index: int  # 0-based
    timestamp_s: float  # seconds from video start
    path: Path


def extract_frames(video_path: Path, out_dir: Path, fps: int = 2, quality: int = 4) -> list[Frame]:
    """Extract frames from video at the specified fps using ffmpeg.

    Returns frames sorted by timestamp.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    pattern = out_dir / "frame_%06d.jpg"

    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(video_path),
        "-vf",
        f"fps={fps}",
        "-q:v",
        str(quality),
        "-loglevel",
        "error",
        str(pattern),
    ]
    subprocess.run(cmd, check=True)

    files = sorted(out_dir.glob("frame_*.jpg"))
    interval = 1.0 / fps
    return [Frame(index=i, timestamp_s=i * interval, path=p) for i, p in enumerate(files)]
