"""Entry point — starts RunPod handler or local FastAPI server based on MODE."""

from src.config import settings
from src.logging import init_sentry, init_logfire

init_sentry()
init_logfire()

if settings.MODE == "local":
    import uvicorn
    from src.server import app

    uvicorn.run(app, host="0.0.0.0", port=settings.PORT)
else:
    from src.handler import start_handler

    start_handler()
