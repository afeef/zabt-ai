# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2025-2026 Afeef Janjua
from zabt_vision.pipeline.candidates import generate_candidates
from zabt_vision.pipeline.signals.transcript_hints import TranscriptHint


def test_candidate_when_two_signals_agree():
    candidates = generate_candidates(
        frame_timestamps=[0.0, 0.5, 1.0, 1.5, 2.0],
        phash_distances=[2, 15, 3, 4],  # spike between 0.5 and 1.0
        ocr_distances=[0.0, 0.8, 0.0, 0.0],  # also spike there
        scene_boundaries=[],
        transcript_hints=[],
        phash_threshold=8,
        ocr_threshold=0.3,
        min_signals=2,
    )
    # Spike at frame index 1→2 (timestamp 1.0)
    times = [c.timestamp_s for c in candidates]
    assert 1.0 in times


def test_no_candidate_when_only_one_weak_signal():
    candidates = generate_candidates(
        frame_timestamps=[0.0, 0.5, 1.0],
        phash_distances=[2, 9],  # just over phash threshold
        ocr_distances=[0.0, 0.0],  # no OCR change
        scene_boundaries=[],
        transcript_hints=[],
        phash_threshold=8,
        ocr_threshold=0.3,
        min_signals=2,
    )
    assert candidates == []


def test_strong_single_signal_still_emits_candidate():
    # min_signals=2, but a scene-detect boundary is very strong on its own
    candidates = generate_candidates(
        frame_timestamps=[0.0, 0.5, 1.0, 1.5],
        phash_distances=[1, 1, 1],
        ocr_distances=[0.0, 0.0, 0.0],
        scene_boundaries=[1.0],
        transcript_hints=[],
        phash_threshold=8,
        ocr_threshold=0.3,
        min_signals=2,
    )
    times = [c.timestamp_s for c in candidates]
    assert any(abs(t - 1.0) < 0.3 for t in times)


def test_transcript_hint_alone_not_enough_but_with_phash_yes():
    candidates = generate_candidates(
        frame_timestamps=[0.0, 0.5, 1.0, 1.5],
        phash_distances=[1, 12, 1],  # spike at 1.0
        ocr_distances=[0.0, 0.0, 0.0],
        scene_boundaries=[],
        transcript_hints=[TranscriptHint(timestamp_s=0.9, phrase="show you", strength=0.9)],
        phash_threshold=8,
        ocr_threshold=0.3,
        min_signals=2,
    )
    times = [c.timestamp_s for c in candidates]
    assert 1.0 in times


def test_candidate_records_which_signals_fired():
    candidates = generate_candidates(
        frame_timestamps=[0.0, 0.5, 1.0],
        phash_distances=[1, 20],
        ocr_distances=[0.0, 0.7],
        scene_boundaries=[],
        transcript_hints=[],
        phash_threshold=8,
        ocr_threshold=0.3,
        min_signals=2,
    )
    assert candidates[0].signals_fired == frozenset({"phash", "ocr"})
