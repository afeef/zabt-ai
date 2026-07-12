import json
import logging
from dataclasses import asdict
from pathlib import Path
from typing import Annotated, Any, Dict, List

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from app.services.transcription.types import TranscriptionConfig, TranscriptionResult

err_console = Console(stderr=True)


def _format_time(seconds: float) -> str:
    minutes = int(seconds // 60)
    secs = seconds % 60
    return f"{minutes:02d}:{secs:04.1f}"


def _print_transcript(result: TranscriptionResult) -> None:
    console = Console()

    console.print("\n[bold]Transcription Results[/bold]")
    console.print("=" * 40)

    for seg in result.segments:
        console.print(
            f"\n[dim][{_format_time(seg.start)} - {_format_time(seg.end)}][/dim] "
            f"[bold cyan]{seg.speaker or 'SPEAKER_UNKNOWN'}[/bold cyan]"
        )
        console.print(f"  {seg.text}")

    console.print("\n" + "-" * 40)
    dur_min = int(result.audio_duration_seconds // 60)
    dur_sec = result.audio_duration_seconds % 60
    console.print(
        f"Language: {result.language}  |  "
        f"Segments: {len(result.segments)}  |  "
        f"Duration: {dur_min}m {dur_sec:.0f}s  |  "
        f"Provider: {result.provider_name}  |  "
        f"Cost: ${result.estimated_cost:.4f}"
    )


def transcribe(
    file: Annotated[
        Path,
        typer.Argument(help="Path to the audio or video file to transcribe"),
    ],
    summarize: Annotated[
        bool,
        typer.Option("--summarize", "-s", help="Run AI summarization after transcription"),
    ] = False,
    json_output: Annotated[
        bool,
        typer.Option("--json", "-j", help="Output results as JSON"),
    ] = False,
    output: Annotated[
        Path | None,
        typer.Option("--output", "-o", help="Write JSON results to a file"),
    ] = None,
    verbose: Annotated[
        bool,
        typer.Option("--verbose", "-v", help="Show detailed provider logs"),
    ] = False,
) -> None:
    """Transcribe an audio/video file through the full pipeline (transcription, alignment, diarization)."""
    # Validate file exists
    if not file.exists():
        err_console.print(f"[bold red]Error:[/bold red] File not found: {file}")
        raise typer.Exit(code=1)

    if not file.is_file():
        err_console.print(f"[bold red]Error:[/bold red] Not a file: {file}")
        raise typer.Exit(code=1)

    # Configure logging verbosity
    log_level = logging.INFO if verbose else logging.WARNING
    logging.basicConfig(level=log_level, format="%(name)s — %(message)s")

    # Import provider (lazy to avoid heavy imports until needed)
    from app.services.transcription import get_provider

    provider = get_provider()
    tx_config = TranscriptionConfig()

    # Run transcription with progress indicator
    try:
        stage_labels = {
            "transcribing": "Transcribing audio",
            "aligning": "Aligning timestamps",
            "diarizing": "Diarizing speakers",
        }

        stage_order = ["transcribing", "aligning", "diarizing"]
        total_stages = len(stage_order)

        def _resolve_label(stage: str) -> str:
            """Resolve stage to display label with step number, supporting
            dynamic stages like 'transcribing (45% — 2m 30s)'."""
            base_stage = stage.split(" (")[0]
            step_num = stage_order.index(base_stage) + 1 if base_stage in stage_order else None
            prefix = f"[{step_num}/{total_stages}]" if step_num else ""

            if stage in stage_labels:
                return f"{prefix} {stage_labels[stage]}..."
            if stage.startswith("transcribing ("):
                detail = stage[len("transcribing "):]
                return f"{prefix} Transcribing audio... {detail}"
            return f"{prefix} {stage}" if prefix else stage

        if json_output:
            last_stage = {"value": ""}

            def on_status_change(stage: str) -> None:
                label = _resolve_label(stage)
                # Avoid repeating identical lines in JSON mode
                if not stage.startswith(last_stage["value"]):
                    err_console.print(f"  {label}")
                last_stage["value"] = stage.split(" (")[0]

            err_console.print("[dim]Processing...[/dim]")
            result = provider.process_audio(
                str(file), config=tx_config, on_status_change=on_status_change
            )
        else:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=Console(stderr=True),
                transient=True,
            ) as progress:
                task = progress.add_task("Initializing...", total=None)

                def on_status_change(stage: str) -> None:
                    progress.update(task, description=_resolve_label(stage))

                result = provider.process_audio(
                    str(file), config=tx_config, on_status_change=on_status_change
                )
    except FileNotFoundError as e:
        err_console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(code=1)
    except Exception as e:
        err_console.print(f"[bold red]Error during transcription:[/bold red] {e}")
        raise typer.Exit(code=1)

    # Optional summarization
    summary_data = None
    if summarize:
        summary_data = _run_summarization(result)

    # Output results
    if json_output:
        _print_json(result, summary_data)
    else:
        _print_transcript(result)
        if summary_data is not None:
            _print_summary(summary_data)

    # Write JSON to file if --output specified
    if output:
        json_data = _build_json(result, summary_data)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(json_data, indent=2, ensure_ascii=False))
        err_console.print(f"\n[green]Results written to {output}[/green]")


def _run_summarization(result: TranscriptionResult) -> Any:
    """Run AI summarization on transcript. Returns MeetingMinutes or None on failure."""
    from app.services.ai_agent import meeting_agent
    from app.services.style_reader import read_style_examples

    if not result.segments:
        err_console.print("[yellow]Warning:[/yellow] No segments to summarize.")
        return None

    try:
        style_examples = read_style_examples(Path("/media/styles"))
        agent_result = meeting_agent.run_sync(result.text, deps=style_examples)
        return agent_result.data
    except Exception as e:
        err_console.print(
            f"\n[bold red]Summarization failed:[/bold red] {e}\n"
            "[dim]Transcription output is shown above.[/dim]"
        )
        return None


def _print_summary(minutes: Any) -> None:
    """Print MeetingMinutes in human-readable format."""
    console = Console()
    console.print("\n[bold]Meeting Summary[/bold]")
    console.print("=" * 40)

    console.print(f"\n{minutes.summary}")

    if minutes.key_decisions:
        console.print("\n[bold]Key Decisions:[/bold]")
        for i, decision in enumerate(minutes.key_decisions, 1):
            console.print(f"  {i}. {decision}")

    if minutes.action_items:
        console.print("\n[bold]Action Items:[/bold]")
        for item in minutes.action_items:
            owner = item.owner or "Unassigned"
            due = f", Due: {item.due_date}" if item.due_date else ""
            console.print(f"  - {item.description} (Owner: {owner}{due})")

    console.print(f"\nSentiment: {minutes.sentiment}")


def _build_json(result: TranscriptionResult, summary_data: Any) -> Dict[str, Any]:
    """Build the JSON-serialisable dict from results."""
    data: Dict[str, Any] = asdict(result)
    if summary_data is not None:
        data["summary"] = summary_data.model_dump()
    return data


def _print_json(result: TranscriptionResult, summary_data: Any) -> None:
    """Print all results as JSON to stdout."""
    print(json.dumps(_build_json(result, summary_data), indent=2, ensure_ascii=False))
