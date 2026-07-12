# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2025-2026 Afeef Janjua
import base64
import io
from typing import TypeVar

from PIL import Image
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


def _image_to_b64(img: Image.Image) -> str:
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    return base64.b64encode(buf.getvalue()).decode("ascii")


class OllamaInference:
    def __init__(self, model: str, host: str = "http://localhost:11434", client=None):
        self.model = model
        if client is None:
            import ollama

            self._client = ollama.Client(host=host)
        else:
            self._client = client

    def generate(
        self,
        images: list[Image.Image],
        prompt: str,
        schema: type[T] | None = None,
    ) -> str | T:
        encoded = [_image_to_b64(img) for img in images]
        full_prompt = prompt
        if schema is not None:
            full_prompt = (
                f"{prompt}\n\nReturn ONLY valid JSON matching this schema:\n"
                f"{schema.model_json_schema()}"
            )

        response = self._client.chat(
            model=self.model,
            messages=[{"role": "user", "content": full_prompt, "images": encoded}],
            format="json" if schema is not None else None,
        )
        content = response["message"]["content"]
        if schema is None:
            return content
        return schema.model_validate_json(content)
