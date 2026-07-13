import logging
import sys

from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import settings

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    stream=sys.stdout,
    force=True,
)

# Uvicorn already configures its own loggers ("uvicorn", "uvicorn.error",
# "uvicorn.access"). We only need to make sure our application loggers propagate
# to the root logger; forcing their level here guarantees that DEBUG messages
# from app.* modules are visible when LOG_LEVEL=DEBUG.
logging.getLogger("app").setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))

logger = logging.getLogger(__name__)
logger.info("Application starting name=%s env=%s log_level=%s", settings.app_name, settings.app_env, settings.log_level)

app = FastAPI(title=settings.app_name, version="0.1.0")
app.include_router(api_router, prefix="/api/v1")
