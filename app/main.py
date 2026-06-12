"""FastAPI application entrypoint for the Lead Processor MVP."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.config import get_settings
from app.logger import get_logger, setup_logging
from app.middleware import BodySizeLimitMiddleware, SecurityHeadersMiddleware
from app.rate_limit import limiter
from app.routes.leads import router as leads_router
from app.services.storage import init_db

# Wire logging as early as possible — before the app object is created.
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    init_db()
    yield


app = FastAPI(title="Lead Processor", lifespan=lifespan)

# --- Rate limiting ---
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]

# --- Middleware (registered in reverse order of execution) ---
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(BodySizeLimitMiddleware)

# --- CORS ---
_cors_origins = [o.strip() for o in get_settings().cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_methods=["POST"],
    allow_headers=["Content-Type"],
)

logger.info("Lead Processor API starting")


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness check used to verify the service is up."""
    return {"status": "ok"}


app.include_router(leads_router)

