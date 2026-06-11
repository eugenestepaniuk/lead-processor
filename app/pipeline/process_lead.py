from __future__ import annotations

import logging

from pydantic import BaseModel

from app.schemas.ai_result import AIResult
from app.schemas.lead import LeadIn
from app.services.ai import analyze_lead
from app.services.normalize import normalize_lead
from app.services.storage import save_lead
from app.services.telegram import format_lead_message, send_message

logger = logging.getLogger(__name__)


class ProcessResult(BaseModel):
    lead_id: int
    summary: str | None = None
    category: str | None = None
    ai_ran: bool
    notified: bool


def process_lead(lead: LeadIn) -> ProcessResult:
    normalized = normalize_lead(lead)
    logger.debug("Lead normalized")

    ai: AIResult | None = analyze_lead(normalized)
    logger.info("AI step done (ai_ran=%s)", ai is not None)

    logger.debug("Persisting lead")
    try:
        lead_id: int = save_lead(normalized, ai)
    except Exception:
        logger.exception("Lead persistence failed")
        raise
    logger.info("Lead persisted (id=%s)", lead_id)

    message: str = format_lead_message(normalized, ai)
    notified: bool = send_message(message)
    logger.info("Notification step done (notified=%s)", notified)

    logger.info(
        "Lead processed (id=%s, ai_ran=%s, notified=%s)",
        lead_id,
        ai is not None,
        notified,
    )

    return ProcessResult(
        lead_id=lead_id,
        summary=ai.summary if ai is not None else None,
        category=ai.category if ai is not None else None,
        ai_ran=ai is not None,
        notified=notified,
    )

