import imagehash
from PIL import Image


def compute_phash_signal(frames: list[Image.Image]) -> list[int]:
    """Compute Hamming distance between pHash of adjacent frames.

    Returns a list of length N-1 where entry i is distance(hash(i), hash(i+1)).
    Larger = more visual change between frames.
    """
    if len(frames) < 2:
        return []
    hashes = [imagehash.phash(f) for f in frames]
    return [int(hashes[i + 1] - hashes[i]) for i in range(len(hashes) - 1)]
