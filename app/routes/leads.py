"""Router for lead ingestion endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from app.logger import get_logger
from app.schemas.lead import LeadIn

router = APIRouter()
logger = get_logger(__name__)


@router.post("/api/leads")
def create_lead(payload: LeadIn) -> dict[str, Any]:
    """Accept a lead submission, validate via LeadIn, and echo it back.

    Full pipeline orchestration arrives in Block 7.
    """
    logger.info(
        "received valid lead with %d populated fields",
        len(payload.model_dump(exclude_none=True)),
    )
    return {"received": payload.model_dump()}

