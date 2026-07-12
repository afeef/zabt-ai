# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2025-2026 Afeef Janjua
import logging
import shutil
import subprocess
import time
import uuid
from pathlib import Path

from PIL import Image

from zabt_vision.inference.base import VisionInference
from zabt_vision.pipeline.candidates import generate_candidates
from zabt_vision.pipeline.cross_validate import JudgedKeyframe, cross_validate
from zabt_vision.pipeline.extract_frames import extract_frames
from zabt_vision.pipeline.refine_boundaries import refine_boundaries
from zabt_vision.pipeline.signals.ocr_diff import compute_ocr_signal
from zabt_vision.pipeline.signals.phash import compute_phash_signal
from zabt_vision.pipeline.signals.scene_detect import compute_scene_signal
from zabt_vision.pipeline.signals.transcript_hints import compute_transcript_hint_signal
from zabt_vision.pipeline.upload import upload_keyframe_jpg, upload_raw_output_json
from zabt_vision.pipeline.video_native import detect_screen_changes_native
from zabt_vision.settings import Settings
from zabt_vision.types import JobInput, JobResult, VisualSegment

logger = logging.getLogger(__name__)


class PipelineStageError(Exception):
    """Wraps an exception raised inside a named pipeline stage so the caller
    (server.py / Celery task) can populate JobResult.failed_stage for telemetry."""

    def __init__(self, stage: str, original: Exception):
        super().__init__(f"stage={stage}: {type(original).__name__}: {original}")
        self.stage = stage
        self.original = original


def download_video(url: str, dest: Path) -> Path:
    """Download a video URL to disk via curl. Supports presigned S3 URLs."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    if url.startswith("file://"):
        src = Path(url[len("file://") :])
        shutil.copy2(src, dest)
        return dest
    subprocess.run(["curl", "-fsSL", "-o", str(dest), url], check=True)
    return dest


def video_duration_seconds(path: Path) -> float:
    out = subprocess.check_output(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ]
    )
    return float(out.decode().strip())


def _load_frames_as_images(frame_records) -> list[Image.Image]:
    return [Image.open(f.path).convert("RGB") for f in frame_records]


def _make_chunks(
    frame_records,
    images: list[Image.Image],
    chunk_seconds: int,
) -> list[tuple[float, float, list[Image.Image]]]:
    chunks: list[tuple[float, float, list[Image.Image]]] = []
    if not frame_records:
        return chunks
    start_idx = 0
    chunk_start_t = frame_records[0].timestamp_s
    for i, fr in enumerate(frame_records):
        if fr.timestamp_s - chunk_start_t >= chunk_seconds:
            chunks.append((chunk_start_t, frame_records[i - 1].timestamp_s, images[start_idx:i]))
            start_idx = i
            chunk_start_t = fr.timestamp_s
    chunks.append((chunk_start_t, frame_records[-1].timestamp_s, images[start_idx:]))
    return chunks


def _make_rescan(video_path: Path, work_dir: Path):
    def rescan(center_s: float, window: float, fps: int):
        out_dir = work_dir / f"rescan_{center_s:.2f}"
        out_dir.mkdir(parents=True, exist_ok=True)
        start = max(0.0, center_s - window)
        cmd = [
            "ffmpeg",
            "-y",
            "-ss",
            f"{start}",
            "-i",
            str(video_path),
            "-t",
            f"{window * 2}",
            "-vf",
            f"fps={fps}",
            "-q:v",
            "2",
            "-loglevel",
            "error",
            str(out_dir / "frame_%06d.jpg"),
        ]
        subprocess.run(cmd, check=True)
        files = sorted(out_dir.glob("frame_*.jpg"))
        return [
            (start + i * (1.0 / fps), Image.open(p).convert("RGB")) for i, p in enumerate(files)
        ]

    return rescan


def _run_stage(name: str, fn, *args, **kwargs):
    """Run a pipeline stage, wrapping any exception in PipelineStageError so
    the caller can populate JobResult.failed_stage."""
    try:
        return fn(*args, **kwargs)
    except Exception as e:
        raise PipelineStageError(stage=name, original=e) from e


def run_pipeline(
    job: JobInput,
    settings: Settings,
    inference: VisionInference,
    s3_client,
) -> JobResult:
    """End-to-end visual breakdown pipeline. Returns a JobResult.

    Stage failures raise PipelineStageError; the caller (server.py / Celery)
    should catch it and surface `e.stage` as JobResult.failed_stage.
    """
    work_dir = Path(settings.work_dir) / job.meeting_id
    work_dir.mkdir(parents=True, exist_ok=True)
    stage_metrics: dict[str, dict] = {}

    # Stage 1: extract frames
    t0 = time.perf_counter()
    video_path = _run_stage("extract_frames", download_video, job.video_url, work_dir / "video.mp4")
    duration = _run_stage("extract_frames", video_duration_seconds, video_path)
    fps = job.params.get("fps", settings.fps)
    frame_records = _run_stage(
        "extract_frames", extract_frames, video_path, work_dir / "frames", fps=fps
    )
    images = _run_stage("extract_frames", _load_frames_as_images, frame_records)
    stage_metrics["extract_frames"] = {
        "duration_ms": int((time.perf_counter() - t0) * 1000),
        "frame_count": len(frame_records),
        "fps": fps,
        "video_duration_s": duration,
    }

    # Stage 2: signals + candidates
    t0 = time.perf_counter()
    phash = _run_stage("compute_signals", compute_phash_signal, images)
    ocr = _run_stage("compute_signals", compute_ocr_signal, images, use_gpu=settings.ocr_use_gpu)
    scene = _run_stage(
        "compute_signals",
        compute_scene_signal,
        video_path,
        threshold=job.params.get("scenedetect_threshold", settings.scenedetect_threshold),
    )
    hints = _run_stage("compute_signals", compute_transcript_hint_signal, job.transcript)
    candidates = _run_stage(
        "compute_signals",
        generate_candidates,
        frame_timestamps=[f.timestamp_s for f in frame_records],
        phash_distances=phash,
        ocr_distances=ocr,
        scene_boundaries=scene,
        transcript_hints=hints,
        phash_threshold=job.params.get("phash_threshold", settings.phash_threshold),
        ocr_threshold=job.params.get("ocr_diff_threshold", settings.ocr_diff_threshold),
        min_signals=job.params.get("ensemble_min_signals", settings.ensemble_min_signals),
    )
    stage_metrics["compute_signals"] = {
        "duration_ms": int((time.perf_counter() - t0) * 1000),
        "candidate_count": len(candidates),
        "phash_candidates": sum(1 for d in phash if d >= settings.phash_threshold),
        "ocr_candidates": sum(1 for d in ocr if d >= settings.ocr_diff_threshold),
        "scenedetect_candidates": len(scene),
        "transcript_candidates": len(hints),
    }

    # Stage 3: video-native detection
    t0 = time.perf_counter()
    chunks = _make_chunks(frame_records, images, settings.chunk_seconds)
    natives = _run_stage(
        "video_native_detection", detect_screen_changes_native, chunks=chunks, inference=inference
    )
    stage_metrics["video_native_detection"] = {
        "duration_ms": int((time.perf_counter() - t0) * 1000),
        "chunks_processed": len(chunks),
        "detections_count": len(natives),
    }

    # Stage 4: cross-validate
    t0 = time.perf_counter()
    frames_by_ts = {f.timestamp_s: img for f, img in zip(frame_records, images, strict=False)}
    judged = _run_stage(
        "cross_validate",
        cross_validate,
        candidates=candidates,
        native_detections=natives,
        frames_by_timestamp=frames_by_ts,
        transcript=job.transcript,
        inference=inference,
        confidence_threshold=job.params.get("confidence_threshold", settings.confidence_threshold),
    )
    stage_metrics["cross_validate"] = {
        "duration_ms": int((time.perf_counter() - t0) * 1000),
        "candidates_evaluated": len(candidates),
        "kept_count": len(judged),
        "rejected_count": len(candidates) - len(judged),
        "mean_confidence": (sum(k.confidence for k in judged) / len(judged)) if judged else 0.0,
    }

    # Stage 5: boundary refinement
    t0 = time.perf_counter()
    rescan = _make_rescan(video_path, work_dir)
    refined = _run_stage(
        "boundary_refinement",
        refine_boundaries,
        keyframes=judged,
        rescan_window=rescan,
        window_seconds=settings.refinement_window_seconds,
        fps=settings.refinement_fps,
    )
    stage_metrics["boundary_refinement"] = {
        "duration_ms": int((time.perf_counter() - t0) * 1000),
        "boundaries_refined": len(refined),
        "mean_adjustment_ms": int(
            1000
            * (
                sum(
                    abs(r.timestamp_s - j.timestamp_s)
                    for r, j in zip(refined, judged, strict=False)
                )
                / len(refined)
            )
        )
        if refined
        else 0,
    }

    # Build VisualSegments — each segment runs from its keyframe to the next (or end-of-video)
    segments: list[VisualSegment] = []
    boundaries = sorted(refined, key=lambda k: k.timestamp_s)
    # Always start at 0.0 with the first detected screen as the opening segment
    if boundaries and boundaries[0].timestamp_s > 0.5:
        # Insert an implicit opening segment from 0 to first boundary using the first
        # detected keyframe's caption (best available approximation)
        boundaries = [
            JudgedKeyframe(
                timestamp_s=0.0,
                caption=boundaries[0].caption + " (opening)",
                confidence=boundaries[0].confidence,
                reasoning="implicit opening segment before first detected change",
            ),
            *boundaries,
        ]

    for i, kf in enumerate(boundaries):
        end_time = boundaries[i + 1].timestamp_s if i + 1 < len(boundaries) else duration
        seg_id = uuid.uuid4().hex
        # Find nearest extracted frame to the keyframe timestamp for the screenshot
        nearest = min(frames_by_ts.keys(), key=lambda t: abs(t - kf.timestamp_s))
        screenshot_key = upload_keyframe_jpg(
            client=s3_client,
            bucket=settings.s3_bucket,
            owner_id=job.owner_id,
            meeting_id=job.meeting_id,
            segment_id=seg_id,
            image=frames_by_ts[nearest],
        )
        segments.append(
            VisualSegment(
                id=seg_id,
                sequence=i,
                start_time=kf.timestamp_s,
                end_time=end_time,
                screenshot_s3_key=screenshot_key,
                caption=kf.caption,
                confidence=kf.confidence,
            )
        )

    raw_payload = {
        "segments": [s.model_dump() for s in segments],
        "stage_metrics": stage_metrics,
        "candidates": [
            {"timestamp_s": c.timestamp_s, "signals": sorted(c.signals_fired)} for c in candidates
        ],
        "natives": [{"timestamp_s": n.timestamp_s, "caption": n.caption} for n in natives],
        "judged": [
            {"timestamp_s": k.timestamp_s, "caption": k.caption, "confidence": k.confidence}
            for k in judged
        ],
        "refined": [{"timestamp_s": r.timestamp_s, "caption": r.caption} for r in refined],
    }
    raw_key = upload_raw_output_json(
        client=s3_client,
        bucket=settings.s3_bucket,
        owner_id=job.owner_id,
        meeting_id=job.meeting_id,
        payload=raw_payload,
    )

    return JobResult(
        status="completed",
        segments=segments,
        raw_output_s3_key=raw_key,
        model=settings.vision_judge_model,
        params=dict(job.params)
        | {
            "fps": fps,
            "phash_threshold": settings.phash_threshold,
            "ocr_diff_threshold": settings.ocr_diff_threshold,
            "ensemble_min_signals": settings.ensemble_min_signals,
            "confidence_threshold": settings.confidence_threshold,
        },
        stage_metrics=stage_metrics,
    )
