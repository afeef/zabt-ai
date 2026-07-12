"""Entrypoint — start the bot worker FastAPI server."""

import uvicorn
from src.config import settings

if __name__ == "__main__":
    uvicorn.run("src.server:app", host="0.0.0.0", port=settings.PORT, reload=False)
