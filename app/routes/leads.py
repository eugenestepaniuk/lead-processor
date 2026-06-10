"""Router for lead ingestion endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from app.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.post("/api/leads")
def create_lead(payload: dict[str, Any]) -> dict[str, Any]:
    """Accept a lead as raw JSON and echo it back (MVP placeholder).

    Field-level validation arrives in subtask 2.1; pipeline orchestration in Block 7.
    """
    logger.info("Received lead payload with %d top-level field(s)", len(payload))
    return {"received": payload}

