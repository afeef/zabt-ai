# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2025-2026 Afeef Janjua
from unittest.mock import MagicMock

from PIL import Image

from zabt_vision.pipeline.candidates import Candidate
from zabt_vision.pipeline.cross_validate import JudgedKeyframe, cross_validate
from zabt_vision.pipeline.video_native import NativeDetection
from zabt_vision.types import TranscriptLine


def _frame() -> Image.Image:
    return Image.new("RGB", (32, 32), color="red")


def test_kept_when_judge_confident_and_signals_agree():
    fake_inf = MagicMock()
    fake_inf.generate.return_value = type(
        "R",
        (),
        {
            "is_boundary": True,
            "confidence": 0.85,
            "caption": "Login page",
            "reasoning": "clear UI shift",
            "exact_timestamp_refinement_s": 1.0,
        },
    )()

    candidates = [Candidate(timestamp_s=1.0, signals_fired=frozenset({"phash", "ocr"}))]
    frames_by_ts = {1.0: _frame()}
    transcript = [TranscriptLine(speaker="A", text="show you", start=0.5, end=1.5)]

    kept = cross_validate(
        candidates=candidates,
        native_detections=[],
        frames_by_timestamp=frames_by_ts,
        transcript=transcript,
        inference=fake_inf,
        confidence_threshold=0.7,
    )
    assert len(kept) == 1
    assert isinstance(kept[0], JudgedKeyframe)
    assert kept[0].caption == "Login page"


def test_rejected_when_low_confidence():
    fake_inf = MagicMock()
    fake_inf.generate.return_value = type(
        "R",
        (),
        {
            "is_boundary": True,
            "confidence": 0.3,
            "caption": "X",
            "reasoning": "r",
            "exact_timestamp_refinement_s": 1.0,
        },
    )()
    candidates = [Candidate(timestamp_s=1.0, signals_fired=frozenset({"phash", "ocr"}))]
    kept = cross_validate(
        candidates=candidates,
        native_detections=[],
        frames_by_timestamp={1.0: _frame()},
        transcript=[],
        inference=fake_inf,
        confidence_threshold=0.7,
    )
    assert kept == []


def test_rejected_when_judge_says_no_boundary():
    fake_inf = MagicMock()
    fake_inf.generate.return_value = type(
        "R",
        (),
        {
            "is_boundary": False,
            "confidence": 0.9,
            "caption": "",
            "reasoning": "just a tooltip",
            "exact_timestamp_refinement_s": 1.0,
        },
    )()
    candidates = [Candidate(timestamp_s=1.0, signals_fired=frozenset({"phash", "ocr"}))]
    kept = cross_validate(
        candidates=candidates,
        native_detections=[],
        frames_by_timestamp={1.0: _frame()},
        transcript=[],
        inference=fake_inf,
        confidence_threshold=0.7,
    )
    assert kept == []


def test_native_detection_treated_as_corroboration_for_single_signal_candidate():
    fake_inf = MagicMock()
    fake_inf.generate.return_value = type(
        "R",
        (),
        {
            "is_boundary": True,
            "confidence": 0.8,
            "caption": "Pricing",
            "reasoning": "r",
            "exact_timestamp_refinement_s": 1.0,
        },
    )()
    # candidate fired only one signal — but native detection agrees nearby
    candidates = [Candidate(timestamp_s=1.0, signals_fired=frozenset({"phash"}))]
    natives = [NativeDetection(timestamp_s=1.1, caption="Pricing", reasoning="r")]
    kept = cross_validate(
        candidates=candidates,
        native_detections=natives,
        frames_by_timestamp={1.0: _frame()},
        transcript=[],
        inference=fake_inf,
        confidence_threshold=0.7,
    )
    assert len(kept) == 1
