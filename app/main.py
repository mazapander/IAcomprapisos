import logging
import sys

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

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

production = settings.app_env.strip().lower() == "production"
app = FastAPI(
    title=settings.app_name,
    version="0.2.0",
    docs_url=None if production else "/docs",
    redoc_url=None if production else "/redoc",
    openapi_url=None if production else "/openapi.json",
)


@app.middleware("http")
async def security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'; connect-src 'self'; img-src 'self' data:; "
        "frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
    )
    if production:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response
app.include_router(api_router, prefix="/api/v1")
app.mount("/", StaticFiles(directory="app/web", html=True), name="web")
