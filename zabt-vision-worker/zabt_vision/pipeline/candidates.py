# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2025-2026 Afeef Janjua
from dataclasses import dataclass, field

from zabt_vision.pipeline.signals.transcript_hints import TranscriptHint


@dataclass(frozen=True)
class Candidate:
    timestamp_s: float
    signals_fired: frozenset[str]
    signal_strengths: dict[str, float] = field(default_factory=dict)


def _bucket_seconds(t: float, bucket: float = 0.5) -> float:
    """Round to the nearest frame-spacing bucket so signals near each other merge."""
    return round(t / bucket) * bucket


def generate_candidates(
    frame_timestamps: list[float],
    phash_distances: list[int],
    ocr_distances: list[float],
    scene_boundaries: list[float],
    transcript_hints: list[TranscriptHint],
    phash_threshold: int,
    ocr_threshold: float,
    min_signals: int,
) -> list[Candidate]:
    """Combine multiple signals into candidate boundaries.

    A candidate fires when:
      - >= `min_signals` distinct signals agree at a given timestamp, OR
      - any single signal is "very strong" (scene_detect always strong;
        phash >= 2x threshold; ocr >= 0.7).
    """
    bucket_size = (frame_timestamps[1] - frame_timestamps[0]) if len(frame_timestamps) > 1 else 0.5

    # Map: bucketed_timestamp -> {signal_name: strength}
    fired: dict[float, dict[str, float]] = {}

    def _record(timestamp: float, signal: str, strength: float) -> None:
        b = _bucket_seconds(timestamp, bucket_size)
        fired.setdefault(b, {})[signal] = max(fired.get(b, {}).get(signal, 0.0), strength)

    # pHash: distance i is between frame i and i+1, attribute to timestamp of i+1
    for i, d in enumerate(phash_distances):
        if d >= phash_threshold:
            _record(frame_timestamps[i + 1], "phash", min(1.0, d / (phash_threshold * 2)))

    for i, d in enumerate(ocr_distances):
        if d >= ocr_threshold:
            _record(frame_timestamps[i + 1], "ocr", d)

    for b in scene_boundaries:
        _record(b, "scene", 1.0)

    for h in transcript_hints:
        _record(h.timestamp_s, "transcript", h.strength)

    # Decide which buckets become candidates
    candidates: list[Candidate] = []
    for ts in sorted(fired.keys()):
        signals = fired[ts]
        very_strong = (
            ("scene" in signals)
            or (signals.get("phash", 0.0) >= 0.99)  # phash >= 2x threshold
            or (signals.get("ocr", 0.0) >= 0.7)
        )
        if len(signals) >= min_signals or very_strong:
            candidates.append(
                Candidate(
                    timestamp_s=ts,
                    signals_fired=frozenset(signals.keys()),
                    signal_strengths=dict(signals),
                )
            )
    return candidates
