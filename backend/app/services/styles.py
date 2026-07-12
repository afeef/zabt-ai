# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2025-2026 Afeef Janjua
import os
from pathlib import Path
from typing import List
from app.models import StyleProfile, StyleProfileCreate
from app.services.base import BaseService
from app.services.style_reader import parse_pdf, read_style_examples

STYLES_DIR = Path(os.environ.get("STYLES_DIR", "/media/styles"))  # noqa: env override for non-docker dev
STYLES_DIR.mkdir(parents=True, exist_ok=True)


class StyleService(BaseService):
    def create_profile(self, profile_in: StyleProfileCreate, owner_id: int) -> StyleProfile:
        profile = StyleProfile.from_orm(profile_in)
        profile.owner_id = owner_id
        return self.save(profile)

    def get_profiles(self, owner_id: int) -> List[StyleProfile]:
        return self.get_all(StyleProfile, owner_id)

    def parse_pdf(self, file_path: Path) -> str:
        return parse_pdf(file_path)

    def get_style_examples(self) -> list[str]:
        """Return a list of style example texts extracted from PDFs in the styles directory."""
        return read_style_examples(STYLES_DIR)


style_service = StyleService()
