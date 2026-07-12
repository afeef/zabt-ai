# Research: Transcription CLI

**Branch**: `012-transcription-cli` | **Date**: 2026-02-26

## R1: CLI Framework — Typer

**Decision**: Use Typer (>= 0.22.0) as the CLI framework.

**Rationale**:
- Constitution Principle VIII mandates Typer for all CLIs
- Typer bundles Rich as a required dependency (since v0.22.0) — no separate
  install needed for terminal formatting, spinners, and tables
- Type-annotated function parameters align with Pydantic and FastAPI patterns
- `typer.testing.CliRunner` provides programmatic testing without subprocesses

**Alternatives considered**:
- `click`: Typer is built on Click; using Click directly adds boilerplate without benefit
- `argparse`: Standard library, but no type-hint integration and verbose configuration
- `python-fire`: Auto-generates CLI from functions but lacks argument validation and help customization

## R2: Entry Point Registration

**Decision**: Register CLI via `[project.scripts]` in pyproject.toml.

**Rationale**:
- `zabt = "app.cli:app"` creates an installable console entry point
- Works with `uv run zabt transcribe ...` in development
- Also supports `python -m app.cli` via `__main__.py` for debugging

**Syntax**:
```toml
[project.scripts]
zabt = "app.cli:app"
```

**Alternatives considered**:
- `[tool.uv.scripts]`: Dev convenience only, not installable — rejected
- Direct `python -m` only: Less ergonomic for regular use — rejected

## R3: Progress Indicators

**Decision**: Use Rich `Progress` with `SpinnerColumn` for indeterminate phase progress.

**Rationale**:
- Transcription phases are indeterminate (no known total duration ahead of time)
- Rich spinners show active phase name, replacing each phase as it starts
- Rich is already bundled with Typer — zero additional dependencies
- `transient=True` keeps the terminal clean after completion

**Pattern**:
```python
from rich.progress import Progress, SpinnerColumn, TextColumn

with Progress(SpinnerColumn(), TextColumn("{task.description}"), transient=True) as progress:
    task = progress.add_task("Transcribing...", total=None)
    # ... run transcription ...
    progress.update(task, description="Aligning...")
    # ... run alignment ...
```

**Alternatives considered**:
- `typer.progressbar()`: Designed for determinate progress (known total) — not suitable
- Plain `print()` statements: No visual spinner, less polished — rejected for default output
- `tqdm`: Extra dependency, Rich already available — rejected

## R4: Service Layer Reuse Strategy

**Decision**: Import `transcription_service` and `meeting_agent` directly from
existing modules. Extract PDF reading from `StyleService` into standalone utility.

**Rationale — Import chain analysis**:

| Module | Imports DB? | CLI-safe? |
|--------|-----------|-----------|
| `app.services.transcription` | No | Yes |
| `app.services.ai_agent` | No | Yes |
| `app.core.config` (Settings) | No | Yes — all fields have defaults |
| `app.services.styles` | Yes (via BaseService → engine) | No |

- `TranscriptionService.process_audio(path, callback)` — fully standalone, takes a
  local file path and optional status callback, returns `Dict[str, Any]` with segments
- `meeting_agent.run_sync(transcript, deps=styles)` — fully standalone, takes transcript
  text and optional style examples, returns `MeetingMinutes`
- `StyleService.get_concatenated_styles()` — the method itself only reads PDFs from disk,
  but the class inherits `BaseService` which imports `app.db.engine`, triggering DB
  engine creation at import time

**Solution**: Create `app/services/style_reader.py` with a standalone `read_style_examples()`
function. Both `StyleService` and the CLI import this utility. This breaks the DB coupling
without changing the StyleService interface.

**Alternatives considered**:
- Import `style_service` directly: Triggers DB engine import — violates FR-008
- Duplicate PDF reading in CLI: Works but violates DRY — rejected
- Lazy imports in BaseService: Too invasive a refactoring — rejected

## R5: Output Formatting

**Decision**: Use Rich `Console` and `Table` for human-readable output; `json.dumps()`
for structured output.

**Rationale**:
- Rich tables render speaker-labeled segments cleanly with column alignment
- JSON output uses standard library `json.dumps(indent=2)` for piping to other tools
- `--json` flag toggles between the two modes (Typer `bool` option)

**Alternatives considered**:
- Plain `print()` with manual formatting: Less readable — rejected
- `rich.print_json()`: Good for JSON display but redundant with plain `json.dumps()` for piping

## R6: Error Handling

**Decision**: Use `rich.console.Console(stderr=True)` for error messages, `raise typer.Exit(code=1)` for non-zero exit codes.

**Rationale**:
- Errors go to stderr (won't interfere with JSON output piped to other tools)
- `typer.Exit(code=1)` ensures shell scripts can detect failures via `$?`
- Typer's built-in pretty exception handler (via Rich) catches unhandled errors
  with clean formatting

## R7: Testing Strategy

**Decision**: Use `typer.testing.CliRunner` for unit tests.

**Rationale**:
- `CliRunner` invokes the Typer app in-process without spawning a subprocess
- Returns `result.exit_code` and `result.output` for assertions
- Can mock `transcription_service.process_audio()` to avoid loading ML models in tests
