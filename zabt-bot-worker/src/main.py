# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2025-2026 Afeef Janjua
"""Entrypoint — start the bot worker FastAPI server."""

import uvicorn
from src.config import settings

if __name__ == "__main__":
    uvicorn.run("src.server:app", host="0.0.0.0", port=settings.PORT, reload=False)
