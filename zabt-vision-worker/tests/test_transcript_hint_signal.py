from zabt_vision.pipeline.signals.transcript_hints import compute_transcript_hint_signal
from zabt_vision.types import TranscriptLine


def test_detects_show_phrase():
    transcript = [
        TranscriptLine(
            speaker="A", text="So let me show you the pricing page", start=10.0, end=12.5
        ),
    ]
    hits = compute_transcript_hint_signal(transcript)
    assert len(hits) == 1
    assert 9.0 < hits[0].timestamp_s < 11.0  # near start of phrase
    assert hits[0].strength > 0


def test_detects_switching_phrase():
    transcript = [
        TranscriptLine(
            speaker="A", text="Now switching over to the dashboard", start=20.0, end=22.0
        ),
    ]
    hits = compute_transcript_hint_signal(transcript)
    assert len(hits) == 1


def test_ignores_unrelated_text():
    transcript = [
        TranscriptLine(speaker="A", text="And then we discussed the budget", start=5.0, end=7.0),
    ]
    hits = compute_transcript_hint_signal(transcript)
    assert hits == []
