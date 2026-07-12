import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from zabt_vision.cli import app
from zabt_vision.types import JobResult, VisualSegment

runner = CliRunner()


def _fake_result() -> JobResult:
    return JobResult(
        status="completed",
        segments=[
            VisualSegment(
                id="seg1",
                sequence=0,
                start_time=0.0,
                end_time=5.0,
                screenshot_s3_key="users/u/meetings/m/visual/seg1.jpg",
                caption="Login page",
                confidence=0.85,
            ),
            VisualSegment(
                id="seg2",
                sequence=1,
                start_time=5.0,
                end_time=12.0,
                screenshot_s3_key="users/u/meetings/m/visual/seg2.jpg",
                caption="Pricing page",
                confidence=0.91,
            ),
        ],
        raw_output_s3_key="users/u/meetings/m/visual/raw_output.json",
        model="qwen3-vl:8b-thinking",
        params={"fps": 2},
        stage_metrics={
            "extract_frames": {"duration_ms": 1000, "frame_count": 10},
            "compute_signals": {"duration_ms": 500, "candidate_count": 4},
            "video_native_detection": {"duration_ms": 8000, "detections_count": 2},
            "cross_validate": {"duration_ms": 12000, "candidates_evaluated": 4, "kept_count": 2},
            "boundary_refinement": {"duration_ms": 1500, "boundaries_refined": 2},
        },
    )


def test_run_command_with_real_video_path(tmp_path: Path):
    fake_video = tmp_path / "demo.mp4"
    fake_video.write_bytes(b"fake")

    with (
        patch("zabt_vision.cli.run_pipeline", return_value=_fake_result()) as mock_run,
        patch("zabt_vision.cli.make_inference", return_value=MagicMock()),
        patch("zabt_vision.cli.make_s3_client", return_value=MagicMock()),
    ):
        result = runner.invoke(app, ["run", str(fake_video), "--fps", "2", "--no-upload"])

    assert result.exit_code == 0, result.output
    assert "Login page" in result.output
    assert "Pricing page" in result.output
    assert "extract_frames" in result.output
    job_arg = mock_run.call_args.kwargs["job"]
    assert job_arg.video_url == f"file://{fake_video.absolute()}"


def test_run_command_rejects_missing_video():
    result = runner.invoke(app, ["run", "/does/not/exist.mp4"])
    assert result.exit_code != 0
    assert "does not exist" in result.output.lower() or "no such file" in result.output.lower()


def test_run_command_threshold_overrides_reach_settings(tmp_path: Path):
    fake_video = tmp_path / "demo.mp4"
    fake_video.write_bytes(b"fake")

    with (
        patch("zabt_vision.cli.run_pipeline", return_value=_fake_result()) as mock_run,
        patch("zabt_vision.cli.make_inference", return_value=MagicMock()),
        patch("zabt_vision.cli.make_s3_client", return_value=MagicMock()),
    ):
        result = runner.invoke(
            app,
            [
                "run",
                str(fake_video),
                "--fps",
                "3",
                "--phash",
                "10",
                "--ocr",
                "0.4",
                "--min-signals",
                "3",
                "--confidence",
                "0.8",
                "--model",
                "qwen3-vl:32b-thinking",
                "--no-upload",
            ],
        )

    assert result.exit_code == 0, result.output
    settings_arg = mock_run.call_args.kwargs["settings"]
    assert settings_arg.fps == 3
    assert settings_arg.phash_threshold == 10
    assert settings_arg.ocr_diff_threshold == 0.4
    assert settings_arg.ensemble_min_signals == 3
    assert settings_arg.confidence_threshold == 0.8
    assert settings_arg.vision_judge_model == "qwen3-vl:32b-thinking"


def test_run_command_loads_transcript_from_file(tmp_path: Path):
    fake_video = tmp_path / "demo.mp4"
    fake_video.write_bytes(b"fake")
    transcript_file = tmp_path / "transcript.json"
    transcript_file.write_text(
        json.dumps(
            [
                {"speaker": "A", "text": "let me show you the dashboard", "start": 1.0, "end": 3.0},
            ]
        )
    )

    with (
        patch("zabt_vision.cli.run_pipeline", return_value=_fake_result()) as mock_run,
        patch("zabt_vision.cli.make_inference", return_value=MagicMock()),
        patch("zabt_vision.cli.make_s3_client", return_value=MagicMock()),
    ):
        result = runner.invoke(
            app,
            [
                "run",
                str(fake_video),
                "--transcript",
                str(transcript_file),
                "--no-upload",
            ],
        )

    assert result.exit_code == 0, result.output
    job_arg = mock_run.call_args.kwargs["job"]
    assert len(job_arg.transcript) == 1
    assert job_arg.transcript[0].text == "let me show you the dashboard"


def test_run_command_emits_json_when_requested(tmp_path: Path):
    fake_video = tmp_path / "demo.mp4"
    fake_video.write_bytes(b"fake")

    with (
        patch("zabt_vision.cli.run_pipeline", return_value=_fake_result()),
        patch("zabt_vision.cli.make_inference", return_value=MagicMock()),
        patch("zabt_vision.cli.make_s3_client", return_value=MagicMock()),
    ):
        result = runner.invoke(app, ["run", str(fake_video), "--json", "--no-upload"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["status"] == "completed"
    assert len(payload["segments"]) == 2


def test_serve_command_starts_uvicorn():
    with patch("zabt_vision.cli.uvicorn.run") as mock_uvicorn:
        result = runner.invoke(app, ["serve", "--host", "127.0.0.1", "--port", "8003"])

    assert result.exit_code == 0, result.output
    mock_uvicorn.assert_called_once()
    kwargs = mock_uvicorn.call_args.kwargs
    assert kwargs["host"] == "127.0.0.1"
    assert kwargs["port"] == 8003
