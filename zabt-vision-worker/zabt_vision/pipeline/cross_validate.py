import logging
from dataclasses import dataclass

from PIL import Image
from pydantic import BaseModel

from zabt_vision.inference.base import VisionInference
from zabt_vision.pipeline.candidates import Candidate
from zabt_vision.pipeline.video_native import NativeDetection
from zabt_vision.types import TranscriptLine

logger = logging.getLogger(__name__)


class _JudgeSchema(BaseModel):
    is_boundary: bool
    confidence: float
    caption: str
    reasoning: str
    exact_timestamp_refinement_s: float


@dataclass(frozen=True)
class JudgedKeyframe:
    timestamp_s: float
    caption: str
    confidence: float
    reasoning: str


_PROMPT_TMPL = """You are analyzing whether a candidate frame represents a meaningful
SCREEN CHANGE in a product-demo / screen-recording video.

PREVIOUS KEPT KEYFRAME caption: {prev_caption}
CANDIDATE timestamp: {ts:.2f}s
SIGNALS THAT FIRED: {signals}
NEARBY VIDEO-NATIVE DETECTION: {native_caption}
TRANSCRIPT NEAR THIS TIMESTAMP:
{transcript_excerpt}

Two images attached:
- Image 1: previous kept keyframe (for context)
- Image 2: candidate frame to judge

Decide: is the candidate a MEANINGFUL screen change worth showing the viewer
(new app, new page, new content section, demo step transition)?
NOT meaningful: cursor moves, scrolling within the same page, hover states,
tooltips, brief modals.

Output JSON matching the schema. `exact_timestamp_refinement_s` should be
your best estimate of the true transition time in seconds (use the candidate
timestamp if unsure)."""


def _transcript_excerpt(
    transcript: list[TranscriptLine], around_s: float, window: float = 10.0
) -> str:
    lines = [
        f"  [{line.start:.1f}s] {line.speaker}: {line.text}"
        for line in transcript
        if (around_s - window) <= line.start <= (around_s + window)
    ]
    return "\n".join(lines) if lines else "  (none)"


def _native_near(
    natives: list[NativeDetection], ts: float, window: float = 2.0
) -> NativeDetection | None:
    for n in natives:
        if abs(n.timestamp_s - ts) <= window:
            return n
    return None


def cross_validate(
    candidates: list[Candidate],
    native_detections: list[NativeDetection],
    frames_by_timestamp: dict[float, Image.Image],
    transcript: list[TranscriptLine],
    inference: VisionInference,
    confidence_threshold: float,
) -> list[JudgedKeyframe]:
    """Single structured call per candidate. Keep candidates whose judge
    output passes confidence threshold AND has corroboration."""
    kept: list[JudgedKeyframe] = []
    prev_caption = "(none — this would be the first keyframe)"
    prev_image: Image.Image | None = None

    candidates = sorted(candidates, key=lambda c: c.timestamp_s)

    for cand in candidates:
        cand_img = frames_by_timestamp.get(cand.timestamp_s)
        if cand_img is None:
            logger.warning("no frame found for candidate at %.2fs", cand.timestamp_s)
            continue

        native = _native_near(native_detections, cand.timestamp_s)
        signals = ", ".join(sorted(cand.signals_fired)) or "(none)"
        prompt = _PROMPT_TMPL.format(
            prev_caption=prev_caption,
            ts=cand.timestamp_s,
            signals=signals,
            native_caption=native.caption if native else "(none)",
            transcript_excerpt=_transcript_excerpt(transcript, cand.timestamp_s),
        )

        images = [prev_image, cand_img] if prev_image is not None else [cand_img]
        try:
            judged = inference.generate(images=images, prompt=prompt, schema=_JudgeSchema)
        except Exception as e:
            logger.warning("judge call failed for candidate at %.2fs: %s", cand.timestamp_s, e)
            continue

        if not judged.is_boundary:
            continue
        if judged.confidence < confidence_threshold:
            continue

        # Require corroboration: ensemble OR native agreement
        has_ensemble = len(cand.signals_fired) >= 2
        has_native = native is not None
        if not (has_ensemble or has_native):
            continue

        kept.append(
            JudgedKeyframe(
                timestamp_s=judged.exact_timestamp_refinement_s or cand.timestamp_s,
                caption=judged.caption,
                confidence=judged.confidence,
                reasoning=judged.reasoning,
            )
        )
        prev_caption = judged.caption
        prev_image = cand_img

    return kept
