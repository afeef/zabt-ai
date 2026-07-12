# Tasks: Transcription CLI

**Input**: Design documents from `/specs/012-transcription-cli/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, quickstart.md

**Tests**: Not explicitly requested — test tasks omitted. Unit tests can be added via `/speckit.checklist` or a follow-up `/speckit.tasks` run.

**Organization**: Tasks grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Add Typer dependency and create CLI module skeleton

- [x] T001 [P] Add `typer>=0.22.0` to dependencies list in backend/pyproject.toml and add `[project.scripts]` section with entry `zabt = "app.cli:app"`
- [x] T002 [P] Create backend/app/cli/__init__.py with a `typer.Typer()` app instance (name="zabt", help="Zabt CLI tools") and backend/app/cli/__main__.py that imports and calls `app()` for `python -m app.cli` support

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Extract PDF reading into a standalone utility so the CLI can read style examples without importing the database engine

**CRITICAL**: No user story work can begin until this phase is complete

- [x] T003 Create backend/app/services/style_reader.py with a standalone `read_style_examples(styles_dir: Path) -> str` function that reads all PDF files from the given directory using pypdf, concatenates their text with `--- Example Style (from filename.pdf) ---` headers, and returns the result. This function must NOT import anything from app.db or app.services.base — it uses only pypdf and pathlib.
- [x] T004 Refactor backend/app/services/styles.py so that `StyleService.get_concatenated_styles()` delegates to `style_reader.read_style_examples(STYLES_DIR)` instead of implementing PDF reading inline. The `parse_pdf()` method should also move to style_reader as a module-level function. Verify that StyleService's existing DB-dependent methods (create_profile, get_profiles) are unaffected.

**Checkpoint**: Foundation ready — user story implementation can begin

---

## Phase 3: User Story 1 — Direct File Transcription (Priority: P1) MVP

**Goal**: Developer can run `uv run zabt transcribe path/to/audio.mp3` and see speaker-labeled, timestamped transcript output with progress indicators

**Independent Test**: Run CLI with a sample audio file (WAV or MP3) and verify segments print to terminal with speaker labels and timestamps

### Implementation for User Story 1

- [x] T005 [US1] Implement the `transcribe` command in backend/app/cli/transcribe.py. The command must: (1) Accept a file path as a required Typer `Argument` with type `Path`, (2) Validate the file exists — if not, print error to stderr via `rich.console.Console(stderr=True)` and `raise typer.Exit(code=1)`, (3) Import and call `transcription_service.process_audio(str(file_path), on_status_change=callback)` where the callback updates a Rich `Progress` spinner (using `SpinnerColumn` + `TextColumn`, `transient=True`) to show the current phase ("Transcribing...", "Aligning...", "Diarizing..."), (4) After completion, display results in human-readable format: each segment as `[MM:SS.s - MM:SS.s] SPEAKER_LABEL\n  text`, followed by a summary line with language, segment count, and total duration, (5) Wrap the `process_audio()` call in try/except to catch processing errors — print the error to stderr and `raise typer.Exit(code=1)`. Reference data-model.md for the segment dict structure (`text`, `speaker`, `start`, `end`, `words`).
- [x] T006 [US1] Register the transcribe command in backend/app/cli/__init__.py by importing `transcribe_app` from `app.cli.transcribe` and adding it via `app.add_typer()` or directly importing and registering the command function

**Checkpoint**: `uv run zabt transcribe sample.mp3` produces speaker-labeled transcript — US1 complete

---

## Phase 4: User Story 2 — Optional AI Summarization (Priority: P2)

**Goal**: Developer can add `--summarize` flag to additionally produce meeting minutes (summary, decisions, action items, sentiment)

**Independent Test**: Run CLI with `--summarize` flag and verify summary output appears after transcript

### Implementation for User Story 2

- [x] T007 [US2] Add a `--summarize` / `-s` option (Typer `Option`, default `False`) to the transcribe command in backend/app/cli/transcribe.py. When enabled: (1) Concatenate all segment text as `[SPEAKER] text\n` lines (same format as worker.py), (2) Import and call `read_style_examples()` from `app.services.style_reader` with `Path("/media/styles")`, (3) Import and call `meeting_agent.run_sync(transcript_text, deps=style_examples)` from `app.services.ai_agent`, (4) Display the `MeetingMinutes` result: summary text, numbered key decisions, action items with owner and due date, sentiment, (5) Wrap summarization in try/except — if it fails, still display the transcript output and print the summarization error to stderr (do NOT raise typer.Exit so transcript is preserved). When `--summarize` is not set, skip all summarization logic entirely.

**Checkpoint**: `uv run zabt transcribe sample.mp3 --summarize` produces transcript + meeting minutes — US2 complete

---

## Phase 5: User Story 3 — Output Format Options (Priority: P3)

**Goal**: Developer can add `--json` flag to output all results as valid JSON for piping to other tools

**Independent Test**: Run CLI with `--json` flag and verify output is valid JSON parseable by `jq`

### Implementation for User Story 3

- [x] T008 [US3] Add a `--json` / `-j` option (Typer `Option`, default `False`) to the transcribe command in backend/app/cli/transcribe.py. When enabled: (1) Suppress the Rich progress spinner (use a simple print-based callback or no visual progress), (2) After processing, build a dict with key `"segments"` (list of segment dicts from process_audio result) and `"language"`, (3) If `--summarize` is also enabled, add a `"summary"` key containing the MeetingMinutes as a dict (use `.model_dump()` since it's a Pydantic model), (4) Print the dict via `json.dumps(output, indent=2, ensure_ascii=False)` to stdout, (5) Ensure NO Rich/styled output goes to stdout when `--json` is active — errors still go to stderr. When `--json` is not set, use the existing human-readable format from US1/US2.

**Checkpoint**: `uv run zabt transcribe sample.mp3 --json | jq .` produces valid JSON — US3 complete

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Verify everything works end-to-end and import isolation is maintained

- [x] T009 [P] Run `cd backend && uv sync` to install the new typer dependency and register the console script, then run `uv run zabt --help` and `uv run zabt transcribe --help` to verify CLI registration and help text generation
- [x] T010 [P] Verify import isolation: run `cd backend && uv run python -c "from app.cli import app; print('CLI imported successfully')"` without any database, MinIO, or Redis running to confirm the CLI module chain does not trigger DB engine creation (FR-008). If it fails, trace the import chain and fix any transitive DB imports.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational (Phase 2)
- **User Story 2 (Phase 4)**: Depends on US1 completion (extends the transcribe command)
- **User Story 3 (Phase 5)**: Depends on US2 completion (must handle both transcript and summary in JSON)
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) — standalone MVP
- **User Story 2 (P2)**: Depends on US1 (adds `--summarize` flag to existing command)
- **User Story 3 (P3)**: Depends on US2 (JSON mode must handle summary data structure)

### Within Each User Story

- Implementation before registration (T005 before T006)
- Core functionality before optional flags
- Error handling included in each implementation task

### Parallel Opportunities

- T001 and T002 run in parallel (different files)
- T009 and T010 run in parallel (independent verification checks)

---

## Parallel Example: Setup Phase

```bash
# Launch both setup tasks together:
Task: "Add typer dependency to backend/pyproject.toml"
Task: "Create backend/app/cli/__init__.py and __main__.py"
```

## Parallel Example: Polish Phase

```bash
# Launch both verification tasks together:
Task: "Run uv sync and verify zabt --help"
Task: "Verify import isolation without DB"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001, T002)
2. Complete Phase 2: Foundational (T003, T004)
3. Complete Phase 3: User Story 1 (T005, T006)
4. **STOP and VALIDATE**: Run `uv run zabt transcribe sample.mp3` with a real audio file
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → **MVP!** (basic transcription works)
3. Add User Story 2 → Test with `--summarize` → Full pipeline validation
4. Add User Story 3 → Test with `--json` → Developer tooling complete
5. Each story adds value without breaking previous stories

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- US2 and US3 extend the same `transcribe` command created in US1 — sequential dependency
- All tasks modify files within `backend/` only — no frontend changes
- Commit after each phase completion for clean history
