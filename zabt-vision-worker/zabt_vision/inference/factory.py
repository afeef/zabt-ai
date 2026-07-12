from zabt_vision.inference.base import VisionInference
from zabt_vision.inference.ollama_backend import OllamaInference
from zabt_vision.settings import Settings


def make_inference(settings: Settings) -> VisionInference:
    if settings.vision_inference_backend == "ollama":
        return OllamaInference(model=settings.vision_judge_model, host=settings.ollama_host)
    raise NotImplementedError(
        f"Inference backend {settings.vision_inference_backend} not implemented in Plan 1. "
        "Only 'ollama' is supported. See Plan 4 for transformers backend."
    )
