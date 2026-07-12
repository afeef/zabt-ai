from unittest.mock import MagicMock

from PIL import Image
from pydantic import BaseModel

from zabt_vision.inference.ollama_backend import OllamaInference


def test_ollama_inference_returns_text():
    fake_client = MagicMock()
    fake_client.chat.return_value = {"message": {"content": "A login page"}}

    inf = OllamaInference(model="qwen3-vl:8b-thinking", client=fake_client)
    img = Image.new("RGB", (10, 10), color="white")

    out = inf.generate([img], "Describe this screen.")

    assert out == "A login page"
    fake_client.chat.assert_called_once()
    call_kwargs = fake_client.chat.call_args.kwargs
    assert call_kwargs["model"] == "qwen3-vl:8b-thinking"
    assert call_kwargs["messages"][0]["role"] == "user"
    assert "images" in call_kwargs["messages"][0]


def test_ollama_inference_parses_json_when_schema():
    fake_client = MagicMock()
    fake_client.chat.return_value = {
        "message": {
            "content": '{"is_boundary": true, "confidence": 0.9, "caption": "X", "reasoning": "r"}'
        }
    }

    class JudgeResult(BaseModel):
        is_boundary: bool
        confidence: float
        caption: str
        reasoning: str

    inf = OllamaInference(model="qwen3-vl:8b-thinking", client=fake_client)
    img = Image.new("RGB", (10, 10), color="white")
    out = inf.generate([img], "Judge.", schema=JudgeResult)

    assert isinstance(out, JudgeResult)
    assert out.is_boundary is True
    assert out.confidence == 0.9
