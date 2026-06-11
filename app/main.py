"""FastAPI application entrypoint for the Lead Processor MVP."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.logger import get_logger, setup_logging
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

logger.info("Lead Processor API starting")


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness check used to verify the service is up."""
    return {"status": "ok"}


app.include_router(leads_router)


