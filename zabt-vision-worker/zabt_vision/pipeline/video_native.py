import json
import logging
from dataclasses import dataclass

from PIL import Image

from zabt_vision.inference.base import VisionInference

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class NativeDetection:
    timestamp_s: float
    caption: str
    reasoning: str


_PROMPT = """You are analyzing a chunk of a screen-recording / product-demo video.
The chunk shows a sequence of frames sampled from a longer video.

Identify every meaningful screen change in this chunk — moments where the visible
application, page, or content meaningfully shifts. Ignore:
- cursor movement
- minor scrolling within the same page
- text being typed into an existing field
- transient UI like tooltips, hover states

For each detected change, output:
- timestamp_ms: integer milliseconds RELATIVE TO THIS CHUNK START (0 to chunk duration)
- caption: <10 words describing what is now on screen, be specific
- reasoning: why this is a meaningful change

Output ONLY valid JSON of this shape:
{"detections": [{"timestamp_ms": <int>, "caption": "<str>", "reasoning": "<str>"}, ...]}"""


def detect_screen_changes_native(
    chunks: list[tuple[float, float, list[Image.Image]]],
    inference: VisionInference,
) -> list[NativeDetection]:
    """Run video-native screen-change detection over chunks of a video.

    `chunks` is a list of (start_s, end_s, frames) tuples where frames is a sampled
    sequence of PIL images representing the chunk. The caller decides sampling rate.

    Each detection's timestamp is rebased into the global video timeline.
    """
    detections: list[NativeDetection] = []
    for chunk_start, _chunk_end, frames in chunks:
        try:
            raw = inference.generate(images=frames, prompt=_PROMPT)
            payload = json.loads(raw if isinstance(raw, str) else str(raw))
            for d in payload.get("detections", []):
                ts_ms = int(d["timestamp_ms"])
                detections.append(
                    NativeDetection(
                        timestamp_s=chunk_start + (ts_ms / 1000.0),
                        caption=str(d["caption"]),
                        reasoning=str(d.get("reasoning", "")),
                    )
                )
        except (json.JSONDecodeError, KeyError, ValueError, TypeError) as e:
            logger.warning("video-native detection failed for chunk @ %ss: %s", chunk_start, e)
            continue
    return detections
