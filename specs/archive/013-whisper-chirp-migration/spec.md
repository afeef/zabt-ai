# Feature Specification: Whisper-to-Chirp Transcription Migration

**Feature Branch**: `013-whisper-chirp-migration`
**Created**: 2026-02-28
**Status**: Draft
**Input**: User description: "Migrate the transcription backend from OpenAI Whisper API to Google Cloud Speech-to-Text V2 API (Chirp 3 model)"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Cost-Optimized Batch Transcription (Priority: P1)

A Starter-tier user uploads a meeting recording. The system transcribes the audio using
the cheapest available processing path (dynamic batch). The user receives a complete
transcript with speaker labels and word-level timestamps at roughly one-third less than
the cost of the previous transcription provider. The user experience (upload flow,
dashboard, results format) remains identical — the cost reduction is transparent to the
user.

**Why this priority**: This is the primary business driver for the migration — 33% cost
reduction ($0.004/min vs $0.006/min) directly impacts unit economics and enables a
sustainable Starter pricing tier at $0.24/hr.

**Independent Test**: Upload a 30-minute audio file as a Starter-tier user. Verify
the transcript is returned with speaker labels and word-level timestamps. Verify the
internal cost log shows the dynamic batch rate. Verify the response JSON matches the
existing contract shape.

**Acceptance Scenarios**:

1. **Given** a Starter-tier user uploads a 30-minute meeting recording, **When** the
   transcription completes, **Then** the transcript includes speaker labels and
   word-level timestamps, and the internal cost log records $0.004/min rate.
2. **Given** a Starter-tier user uploads an audio file, **When** the transcription
   is processing, **Then** the user sees a status indicator that the job is queued
   (since dynamic batch may take longer than synchronous processing).
3. **Given** the new transcription provider is active, **When** a Starter-tier user
   views their transcript on the dashboard, **Then** the response JSON structure is
   identical to what the previous provider returned.

---

### User Story 2 - Standard-Speed Pro Transcription (Priority: P2)

A Pro-tier user uploads a meeting recording and receives a transcript processed at
standard speed (not dynamic batch). The transcription completes faster than the Starter
tier's batch processing. The transcript includes full speaker diarization and
word-level timestamps.

**Why this priority**: Pro-tier users pay more ($0.96/hr) and expect faster turnaround.
Standard batch processing provides a meaningful speed advantage over dynamic batch
while still being cheaper than the previous provider for the platform.

**Independent Test**: Upload a 30-minute audio file as a Pro-tier user. Verify the
transcript arrives faster than an equivalent Starter-tier job. Verify speaker
diarization and timestamps are present. Verify the cost log shows the standard
batch rate.

**Acceptance Scenarios**:

1. **Given** a Pro-tier user uploads a meeting recording, **When** the transcription
   completes, **Then** the result includes speaker diarization with distinct speaker
   labels and word-level timestamps.
2. **Given** a Pro-tier user and a Starter-tier user upload identical audio files at
   the same time, **When** both jobs complete, **Then** the Pro-tier job completes
   first (standard processing vs dynamic batch).
3. **Given** a Pro-tier user's transcription completes, **When** the cost log is
   checked, **Then** it records the standard batch rate.

---

### User Story 3 - Speaker Diarization for Multi-Speaker Meetings (Priority: P3)

A user uploads a meeting with multiple participants. The system automatically detects
and labels distinct speakers throughout the transcript (e.g., "Speaker 1", "Speaker 2").
Previously, diarization was either unavailable or required a separate processing step.
Now it is natively included in every transcription.

**Why this priority**: Speaker diarization is a high-value feature that transforms
raw transcripts into actionable meeting notes. It enables the downstream summarization
pipeline to produce speaker-attributed summaries, action items, and decisions.

**Independent Test**: Upload a 15-minute recording with 3 distinct speakers. Verify the
transcript labels each segment with the correct speaker. Verify speaker count is between
the configured minimum and maximum.

**Acceptance Scenarios**:

1. **Given** a user uploads a meeting recording with 4 participants, **When** the
   transcription completes, **Then** the transcript contains speaker labels (e.g.,
   "Speaker 1" through "Speaker 4") attributed to the correct audio segments.
2. **Given** a user uploads a recording with a single speaker, **When** the
   transcription completes, **Then** the transcript labels all segments as a single
   speaker (no spurious speaker splits).
3. **Given** speaker diarization is enabled, **When** the transcript is passed to the
   summarization pipeline, **Then** the summarizer can produce speaker-attributed
   summaries.

---

### User Story 4 - Automatic Language Detection (Priority: P4)

A user uploads a meeting recording in a non-English language. The system automatically
detects the spoken language (from 85+ supported languages for transcription) and
transcribes accordingly, without requiring the user to manually select a language.
Note: Speaker diarization is available for 14 languages; for other languages,
transcription is returned without speaker labels.

**Why this priority**: Automatic language detection removes friction for multilingual
teams and expands the addressable market to non-English-speaking users without any UI
changes.

**Independent Test**: Upload recordings in English, Spanish, and Arabic. Verify each
transcript is in the correct language without any manual language selection.

**Acceptance Scenarios**:

1. **Given** a user uploads a recording spoken entirely in Spanish, **When** the
   transcription completes, **Then** the transcript is in Spanish and the detected
   language is recorded in the transcript metadata.
2. **Given** a user uploads a recording in a supported language, **When** no language
   is explicitly selected, **Then** the system automatically detects the language and
   transcribes correctly.

---

### User Story 5 - Automatic Fallback on Provider Failure (Priority: P5)

The primary transcription provider experiences repeated failures (5 consecutive errors).
The system automatically falls back to the previous provider for a cooldown period
(5 minutes), ensuring users are not blocked. When the cooldown expires, the system
retries the primary provider. All of this is transparent to the user.

**Why this priority**: Reliability is critical for a paid service. Users MUST NOT
experience extended outages during the migration period. The fallback mechanism ensures
continuity while the new provider is being validated in production.

**Independent Test**: Simulate 5 consecutive failures from the primary provider. Verify
the system switches to the fallback. After 5 minutes, verify the system retries the
primary provider.

**Acceptance Scenarios**:

1. **Given** the primary transcription provider fails 5 times consecutively, **When** a
   user submits a new transcription request, **Then** the system routes the request to
   the fallback provider and the user receives a successful transcript.
2. **Given** the system is in fallback mode, **When** the 5-minute cooldown expires,
   **Then** the next transcription request is routed to the primary provider.
3. **Given** the system is in fallback mode, **When** a user submits a transcription,
   **Then** the user is not aware of any provider switch — the response format and
   quality remain consistent.

---

### Edge Cases

- What happens when a user uploads an audio file longer than 8 hours? The system MUST
  reject files exceeding the maximum duration with a clear error message.
- What happens when the primary provider and the fallback provider both fail? The system
  MUST return a retriable error to the user with an estimated retry time.
- What happens when audio quality is too poor for speaker diarization? The system MUST
  still return a transcript (without speaker labels) rather than failing entirely.
- What happens when a user uploads an unsupported audio format? The system MUST return
  a clear error listing supported formats.
- What happens when dynamic batch processing exceeds the 24-hour maximum? The system
  MUST notify the user and offer to resubmit.
- What happens when the user's subscription tier changes mid-transcription? The system
  MUST honor the tier that was active at the time of submission.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST transcribe uploaded audio files and return transcripts with
  word-level timestamps (start time, end time per word).
- **FR-002**: System MUST include speaker diarization in all transcriptions, labeling
  distinct speakers with configurable minimum and maximum speaker count.
- **FR-003**: System MUST route Starter-tier users to the cheapest processing path
  (dynamic batch) and Pro-tier users to standard batch processing.
- **FR-004**: System MUST automatically detect the spoken language from 85+ supported
  transcription languages when no language is explicitly specified. Speaker diarization
  is supported for 14 languages; for unsupported diarization languages, the transcript
  MUST still be returned without speaker labels.
- **FR-005**: System MUST upload audio to cloud storage before submitting batch
  transcription requests (batch processing requires cloud-hosted audio URIs for files
  longer than 1 minute).
- **FR-006**: System MUST preserve the existing response format — the frontend-facing
  contract (REST endpoints, response JSON shape) MUST NOT change.
- **FR-007**: System MUST maintain the previous transcription provider as a functional
  fallback behind the same abstraction interface.
- **FR-008**: System MUST implement a circuit breaker: after 5 consecutive failures
  from the primary provider, automatically route requests to the fallback provider for
  a 5-minute cooldown period.
- **FR-009**: System MUST retry transient provider errors (service unavailable, deadline
  exceeded) with exponential backoff before counting toward the circuit breaker.
- **FR-010**: System MUST log structured cost-tracking data for every transcription
  request: audio duration (seconds), recognition method (dynamic batch / standard batch),
  provider name, and estimated cost.
- **FR-011**: System MUST reject audio files exceeding the maximum supported duration
  with a user-friendly error message.
- **FR-012**: System MUST support a feature flag or configuration toggle to switch
  between the primary and fallback transcription providers without code changes.
- **FR-013**: System MUST NOT modify the downstream summarization pipeline — transcripts
  MUST be passed to the summarizer in the same format regardless of which provider
  produced them.
- **FR-014**: System MUST NOT alter the database schema for storing transcripts — only
  the ingestion/parsing layer MUST change.

### Key Entities

- **Transcription Request**: Represents a user-submitted audio file for transcription.
  Key attributes: audio file reference, user ID, subscription tier, requested language
  (optional), submission timestamp, status (queued/processing/completed/failed).
- **Transcription Result**: The output of a transcription job. Key attributes: full
  transcript text, word-level timestamps, speaker labels, detected language, provider
  used, recognition method, audio duration, estimated cost.
- **Provider Configuration**: Controls which transcription provider is active and
  fallback behavior. Key attributes: active provider identifier, fallback provider
  identifier, circuit breaker state (open/closed), consecutive failure count, last
  failure timestamp.

### Assumptions

- The three subscription tiers (Starter, Pro, Business) are already implemented in the
  user/account system and can be queried at transcription time.
- Audio files are already uploaded to object storage (MinIO) before the transcription
  service receives them; the migration adds a secondary upload to cloud storage
  specifically for the new provider's batch processing requirement.
- The existing summarization pipeline accepts transcript text with speaker labels and
  does not depend on provider-specific metadata.
- The "Business tier with real-time streaming" is documented here for completeness but
  is out of scope for this migration — it will be specified as a separate feature when
  the Business tier is launched.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Transcription cost per minute of audio MUST decrease by at least 33%
  for Starter-tier users compared to the current provider ($0.004/min vs $0.006/min).
- **SC-002**: All transcriptions MUST include word-level timestamps with start and end
  times — 100% of completed transcripts MUST contain timestamp data.
- **SC-003**: Speaker diarization MUST correctly identify distinct speakers in at least
  90% of multi-speaker recordings (as validated by manual review of a sample set).
- **SC-004**: The system MUST automatically detect the correct spoken language in at
  least 95% of recordings in the top 20 most-used languages.
- **SC-005**: The existing frontend MUST continue to function without any changes — zero
  frontend modifications required for this migration.
- **SC-006**: Provider failover MUST complete within 1 second of the circuit breaker
  triggering — users MUST NOT experience more than 1 failed request before fallback
  activates.
- **SC-007**: The system MUST successfully transcribe audio files up to 4 hours in
  duration without errors.
- **SC-008**: Pro-tier transcriptions MUST complete at least 2x faster than Starter-tier
  dynamic batch transcriptions for equivalent audio files.
