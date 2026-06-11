"""Router for lead ingestion endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from app.pipeline.process_lead import ProcessResult, process_lead
from app.schemas.lead import LeadIn

router = APIRouter()


@router.post("/api/leads")
def create_lead(payload: LeadIn) -> ProcessResult:
    """Accept a lead submission and run it through the full pipeline."""
    return process_lead(payload)

