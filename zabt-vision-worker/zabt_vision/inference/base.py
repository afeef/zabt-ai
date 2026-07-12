from typing import Protocol, TypeVar

from PIL import Image
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class VisionInference(Protocol):
    def generate(
        self,
        images: list[Image.Image],
        prompt: str,
        schema: type[T] | None = None,
    ) -> str | T:
        """Run a vision-language inference call.

        If `schema` is provided, the model is asked to produce JSON matching
        the schema and the result is parsed into an instance of the schema.
        Otherwise raw text is returned.
        """
        ...
