"""Router for lead ingestion endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Request

from app.pipeline.process_lead import ProcessResult, process_lead
from app.rate_limit import limiter
from app.schemas.lead import LeadIn

router = APIRouter()


@router.post("/api/leads")
@limiter.limit("5/minute")
def create_lead(request: Request, payload: LeadIn) -> ProcessResult:
    """Accept a lead submission and run it through the full pipeline."""
    return process_lead(payload)
