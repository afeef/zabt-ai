from PIL import Image


def _jaccard_distance(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 0.0
    union = a | b
    inter = a & b
    return 1.0 - (len(inter) / len(union))


def _normalize(token: str) -> str:
    return token.strip().lower()


def _extract_tokens(reader, image: Image.Image) -> set[str]:
    import numpy as np

    arr = np.array(image)
    results = reader.readtext(arr)
    tokens: set[str] = set()
    for entry in results:
        # easyocr returns (bbox, text, confidence)
        text = entry[1]
        for word in text.split():
            normalized = _normalize(word)
            if len(normalized) >= 2:  # drop single chars
                tokens.add(normalized)
    return tokens


def compute_ocr_signal(frames: list[Image.Image], reader=None, use_gpu: bool = True) -> list[float]:
    """For each adjacent pair of frames, compute Jaccard distance between
    the sets of OCR tokens. Larger = more text change.

    `use_gpu` is forwarded to easyocr.Reader when constructing a default reader.
    Set to False on CPU-only hosts. Ignored when `reader` is provided."""
    if len(frames) < 2:
        return []

    if reader is None:
        import easyocr

        reader = easyocr.Reader(["en"], gpu=use_gpu, verbose=False)

    token_sets = [_extract_tokens(reader, f) for f in frames]
    return [_jaccard_distance(token_sets[i], token_sets[i + 1]) for i in range(len(token_sets) - 1)]
