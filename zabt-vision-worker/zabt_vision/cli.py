"""Typer CLI for zabt-vision-worker.

Shares Pydantic types (JobInput, Settings, JobResult) and the run_pipeline
entrypoint with server.py — same code paths, different invocation surface.
"""

import json
from pathlib import Path
from typing import Annotated

import typer
import uvicorn
from rich.console import Console
from rich.table import Table

from zabt_vision.inference.factory import make_inference
from zabt_vision.pipeline.run import run_pipeline
from zabt_vision.pipeline.upload import make_s3_client
from zabt_vision.settings import Settings
from zabt_vision.types import JobInput, JobResult, TranscriptLine


class _NullS3:
    """No-op S3 stand-in for `--no-upload` calibration runs.

    Pipeline calls only `put_object(**kwargs)` on the client; this swallows
    those calls so we don't hit real S3 (and don't need credentials) while
    iterating on thresholds.
    """

    def put_object(self, **_kwargs) -> None:
        pass


app = typer.Typer(
    name="zabt-vision",
    help="Local CLI for the zabt-vision-worker service. "
    "Runs the same pipeline as the FastAPI server.",
    no_args_is_help=True,
    add_completion=False,
)
console = Console()


def _build_settings(
    fps: int,
    phash: int,
    ocr: float,
    scene: float,
    min_signals: int,
    confidence: float,
    model: str | None,
    work_dir: Path | None,
) -> Settings:
    overrides: dict = {
        "fps": fps,
        "phash_threshold": phash,
        "ocr_diff_threshold": ocr,
        "scenedetect_threshold": scene,
        "ensemble_min_signals": min_signals,
        "confidence_threshold": confidence,
    }
    if model is not None:
        overrides["vision_judge_model"] = model
    if work_dir is not None:
        overrides["work_dir"] = str(work_dir)
    return Settings(**overrides)


def _load_transcript(path: Path | None) -> list[TranscriptLine]:
    if path is None:
        return []
    raw = json.loads(path.read_text())
    return [TranscriptLine.model_validate(line) for line in raw]


def _print_human(result: JobResult) -> None:
    metrics_table = Table(title="Stage metrics", show_header=True, header_style="bold")
    metrics_table.add_column("Stage")
    metrics_table.add_column("Duration (ms)", justify="right")
    metrics_table.add_column("Detail")
    for stage, m in result.stage_metrics.items():
        duration = m.get("duration_ms", "-")
        detail = ", ".join(f"{k}={v}" for k, v in m.items() if k != "duration_ms")
        metrics_table.add_row(stage, str(duration), detail)
    console.print(metrics_table)

    seg_table = Table(
        title=f"Segments ({len(result.segments)})", show_header=True, header_style="bold"
    )
    seg_table.add_column("#", justify="right")
    seg_table.add_column("Start", justify="right")
    seg_table.add_column("End", justify="right")
    seg_table.add_column("Conf", justify="right")
    seg_table.add_column("Caption")
    for s in result.segments:
        seg_table.add_row(
            str(s.sequence),
            f"{s.start_time:.2f}s",
            f"{s.end_time:.2f}s",
            f"{s.confidence:.2f}",
            s.caption,
        )
    console.print(seg_table)

    if result.status == "failed":
        console.print(f"[bold red]FAILED[/]: {result.error}")


@app.command()
def run(
    video: Annotated[
        Path,
        typer.Argument(
            exists=True,
            file_okay=True,
            dir_okay=False,
            resolve_path=True,
            help="Path to the local video file.",
        ),
    ],
    transcript: Annotated[
        Path | None,
        typer.Option(
            "--transcript",
            "-t",
            exists=True,
            file_okay=True,
            dir_okay=False,
            help="Optional JSON file: list of {speaker, text, start, end} objects.",
        ),
    ] = None,
    fps: Annotated[int, typer.Option("--fps", help="Frame extraction rate.")] = 2,
    phash: Annotated[int, typer.Option("--phash", help="pHash distance threshold.")] = 8,
    ocr: Annotated[float, typer.Option("--ocr", help="OCR Jaccard distance threshold.")] = 0.3,
    scene: Annotated[float, typer.Option("--scene", help="PySceneDetect threshold.")] = 27.0,
    min_signals: Annotated[
        int, typer.Option("--min-signals", help="Min agreeing signals for a candidate.")
    ] = 2,
    confidence: Annotated[
        float, typer.Option("--confidence", help="Judge confidence threshold to keep.")
    ] = 0.7,
    model: Annotated[
        str | None, typer.Option("--model", help="Override VISION_JUDGE_MODEL.")
    ] = None,
    work_dir: Annotated[
        Path | None, typer.Option("--work-dir", help="Working directory for frames.")
    ] = None,
    owner_id: Annotated[
        str, typer.Option("--owner-id", help="Synthetic owner_id for the job.")
    ] = "calibrate",
    no_upload: Annotated[
        bool, typer.Option("--no-upload", help="Mock S3 client (no real uploads).")
    ] = False,
    output_json: Annotated[
        bool, typer.Option("--json", help="Emit JobResult as JSON to stdout.")
    ] = False,
) -> None:
    """Run the full pipeline against a local video. Used for calibration and smoke tests."""
    settings = _build_settings(fps, phash, ocr, scene, min_signals, confidence, model, work_dir)
    inference = make_inference(settings)
    s3_client = _NullS3() if no_upload else make_s3_client(settings)

    job = JobInput(
        video_url=f"file://{video.absolute()}",
        owner_id=owner_id,
        meeting_id=video.stem,
        transcript=_load_transcript(transcript),
        params={},
    )

    result = run_pipeline(job=job, settings=settings, inference=inference, s3_client=s3_client)

    if output_json:
        console.print_json(result.model_dump_json())
    else:
        _print_human(result)

    if result.status == "failed":
        raise typer.Exit(code=1)


@app.command()
def serve(
    host: Annotated[str, typer.Option("--host")] = "0.0.0.0",
    port: Annotated[int, typer.Option("--port")] = 8003,
    reload: Annotated[bool, typer.Option("--reload")] = False,
) -> None:
    """Start the FastAPI server (same handler as `uvicorn zabt_vision.server:app`)."""
    uvicorn.run("zabt_vision.server:app", host=host, port=port, reload=reload)


if __name__ == "__main__":
    app()
