import re
from dataclasses import dataclass

from zabt_vision.types import TranscriptLine

# Phrases strongly suggesting a screen change. Each tuple: (regex, strength 0..1).
_PATTERNS: list[tuple[re.Pattern, float]] = [
    (re.compile(r"\blet me show you\b", re.I), 0.9),
    (re.compile(r"\bswitching (over )?to\b", re.I), 0.9),
    (re.compile(r"\bhere'?s the\b", re.I), 0.7),
    (re.compile(r"\blet'?s look at\b", re.I), 0.7),
    (re.compile(r"\bif we look at\b", re.I), 0.7),
    (re.compile(r"\bnext (slide|page|screen)\b", re.I), 0.95),
    (re.compile(r"\bover (here|on the)\b", re.I), 0.5),
    (re.compile(r"\bnow (we|i'?ll|let'?s) (move|go) to\b", re.I), 0.85),
]


@dataclass(frozen=True)
class TranscriptHint:
    timestamp_s: float
    phrase: str
    strength: float


def compute_transcript_hint_signal(transcript: list[TranscriptLine]) -> list[TranscriptHint]:
    hits: list[TranscriptHint] = []
    for line in transcript:
        for pattern, strength in _PATTERNS:
            match = pattern.search(line.text)
            if match:
                # Place hint slightly BEFORE the speaker mentions it (visual usually
                # changes in sync with or just before the words).
                hits.append(
                    TranscriptHint(
                        timestamp_s=max(0.0, line.start - 0.5),
                        phrase=match.group(0),
                        strength=strength,
                    )
                )
                break  # one hint per line max
    return hits
