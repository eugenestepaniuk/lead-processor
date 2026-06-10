"""FastAPI application entrypoint for the Lead Processor MVP."""

from __future__ import annotations

from fastapi import FastAPI

from app.logger import get_logger, setup_logging
from app.routes.leads import router as leads_router

# Wire logging as early as possible — before the app object is created.
setup_logging()
logger = get_logger(__name__)

app = FastAPI(title="Lead Processor")

logger.info("Lead Processor API starting")


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness check used to verify the service is up."""
    return {"status": "ok"}


app.include_router(leads_router)


