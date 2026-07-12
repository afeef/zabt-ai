# Research: YouTube URL Ingestion

## Decision 1: YouTube Audio Extraction Tool

**Decision**: Use `yt-dlp` (fork of youtube-dl) for YouTube audio extraction.

**Rationale**: yt-dlp is the de facto standard for YouTube media extraction. It's actively maintained (weekly releases), handles all YouTube URL formats, extracts metadata, and supports audio-only extraction with format selection. It's a Python package installable via pip and also available as a standalone binary.

**Alternatives considered**:
- `youtube-dl` — original project, now largely unmaintained. yt-dlp is the active fork with better performance and more features.
- `pytube` — Python-only, frequently breaks due to YouTube changes, smaller community.
- YouTube Data API — requires API key, rate limits, doesn't provide audio download capability.

## Decision 2: yt-dlp Integration Pattern

**Decision**: Use yt-dlp as a subprocess call (`subprocess.run`) within a Celery task, not as a Python library.

**Rationale**: yt-dlp's Python API is undocumented and unstable (internal API). The CLI is the stable interface. Subprocess invocation is the recommended approach per yt-dlp docs. This also simplifies error handling (exit codes) and avoids import-time side effects.

**Command pattern**:
```bash
# Extract metadata (no download)
yt-dlp --dump-json --no-download "URL"

# Download best audio
yt-dlp -x --audio-format mp3 --audio-quality 0 -o "/media/tmp/yt_%(id)s.%(ext)s" "URL"
```

**Alternatives considered**:
- yt-dlp Python API (`yt_dlp.YoutubeDL`) — works but undocumented, breaks between versions.
- Direct ffmpeg + HTTP streaming — too complex, doesn't handle YouTube's adaptive streams.

## Decision 3: Worker Architecture

**Decision**: Add a new Celery task `stage_youtube_download` that runs as the first stage in a YouTube-specific pipeline chain, then feeds into the existing `stage_transcribe → stage_summarize` chain.

**Rationale**: Per user clarification, the API must do minimal work. The YouTube download is I/O-bound (network) and can take minutes for long videos. Running it in a separate Celery task (before the existing pipeline) keeps it off the API thread and allows the existing transcription pipeline to remain untouched.

**Pipeline chain**:
```python
# YouTube pipeline
chain(
    stage_youtube_download.s(meeting_id),    # NEW: validate, download audio, extract metadata
    stage_transcribe.s(),                     # EXISTING: unchanged
    stage_summarize.s(),                      # EXISTING: unchanged
)
```

**Alternatives considered**:
- Separate Celery queue for YouTube downloads — adds operational complexity (separate worker config). Not needed initially; a single worker pool handles both YouTube and file uploads.
- Download in API endpoint — rejected per user requirement (API must be lightweight).

## Decision 4: URL Validation Strategy

**Decision**: Two-layer validation:
1. **Frontend (instant)**: Regex match against known YouTube URL patterns. Catches obvious non-YouTube URLs before API call.
2. **Worker (async)**: yt-dlp `--dump-json --no-download` to verify video exists, extract metadata, check duration. Failures surface on meeting card.

**Rationale**: Frontend validation gives instant feedback for clearly wrong URLs. Worker validation catches all edge cases (deleted videos, geo-restrictions, age gates) that can't be detected from URL format alone. This split keeps the API lightweight per the clarified architecture.

**YouTube URL patterns** (frontend regex):
- `youtube.com/watch?v=VIDEO_ID`
- `youtu.be/VIDEO_ID`
- `youtube.com/live/VIDEO_ID`
- `youtube.com/shorts/VIDEO_ID`
- `youtube.com/embed/VIDEO_ID`
- `m.youtube.com/watch?v=VIDEO_ID`
- Reject: `youtube.com/playlist?list=...`

## Decision 5: Meeting Model Extension

**Decision**: Add fields to existing `Meeting` model rather than creating a separate `YouTubeMeeting` table.

**Rationale**: YouTube meetings go through the same lifecycle (queued → processing → completed/failed) and are displayed in the same feed. A separate table would require complex joins and dual-model logic throughout the codebase. Nullable fields on the existing model keep things simple.

**New fields**:
- `source_type: str = "upload"` — "upload" or "youtube"
- `source_url: Optional[str] = None` — original YouTube URL
- `youtube_title: Optional[str] = None` — video title (becomes meeting title)
- `youtube_duration_seconds: Optional[int] = None` — video duration for validation
- `youtube_thumbnail_url: Optional[str] = None` — video thumbnail
- `youtube_channel: Optional[str] = None` — channel name

## Decision 6: Concurrency Limit Implementation

**Decision**: Check active YouTube ingestion count in the API endpoint before creating the meeting. Count meetings with `source_type="youtube"` and `status in ("queued", "processing")` for the authenticated user.

**Rationale**: Simple DB query at creation time. No need for Redis counters or distributed locks — the check is best-effort (race condition window is tiny and consequence is just 4 concurrent instead of 3, which is acceptable).

**Alternatives considered**:
- Redis atomic counter — overkill for a soft limit.
- Celery rate limiting — doesn't limit per-user, only per-task.

## Decision 7: Docker Installation

**Decision**: Install yt-dlp via pip in the worker Docker target only. Also install ffmpeg (required by yt-dlp for audio extraction/conversion).

**Rationale**: yt-dlp is only used in worker tasks. The API container doesn't need it. ffmpeg is already available in the worker image (required by whisper/whisperx).

**Installation**:
```dockerfile
# In worker target stage
RUN pip install yt-dlp
# ffmpeg is already installed (whisper dependency)
```
