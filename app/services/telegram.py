"""Telegram notification service.

Sends plain-text messages to a Telegram chat via the Bot API using httpx.
Error handling (try/except) is added in subtask 6.3.
"""

from __future__ import annotations

import logging

import httpx

from app.config import get_settings
from app.schemas.ai_result import AIResult
from app.schemas.lead import LeadIn

logger = logging.getLogger(__name__)

_TELEGRAM_TIMEOUT_SECONDS = 10.0


# ---------------------------------------------------------------------------
# HTML formatting helpers
# ---------------------------------------------------------------------------


def _escape_html(value: str) -> str:
    """Escape the 3 characters that are special in Telegram HTML parse mode.

    Order matters: & must be replaced first so the & in &lt;/&gt; is not
    double-escaped.
    """
    return value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def format_lead_message(lead: LeadIn, ai: AIResult | None) -> str:
    """Build an HTML-formatted Telegram message for a processed lead.

    Only fields that are present (not None / not empty) are included.
    All dynamic values are escaped with _escape_html; static HTML tags are not.
    The AI block (category + summary) is omitted entirely when *ai* is None.
    """
    lines: list[str] = ["🔔 <b>New lead</b>"]

    lines.append(f"<b>Name:</b> {_escape_html(lead.name)}")

    if lead.email:
        lines.append(f"<b>Email:</b> {_escape_html(str(lead.email))}")
    if lead.phone:
        lines.append(f"<b>Phone:</b> {_escape_html(lead.phone)}")
    if lead.message:
        lines.append(f"<b>Message:</b> {_escape_html(lead.message)}")
    if lead.source:
        lines.append(f"<b>Source:</b> {_escape_html(lead.source)}")

    if ai is not None:
        lines.append(f"<b>Category:</b> {_escape_html(ai.category)}")
        if ai.summary:
            lines.append(f"<b>Summary:</b> {_escape_html(ai.summary)}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Network sender
# ---------------------------------------------------------------------------


def send_message(text: str) -> bool:
    """Post *text* to the configured Telegram chat using HTML parse mode.

    Returns True when the message was sent, False when Telegram is disabled.
    HTTP errors propagate as-is (error handling is added in subtask 6.3).
    """
    settings = get_settings()

    if not settings.telegram_enabled:
        logger.info("Telegram disabled; skipping notification")
        return False

    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    payload = {"chat_id": settings.telegram_chat_id, "text": text, "parse_mode": "HTML"}

    # Broad except: Telegram is best-effort; any failure must not crash the pipeline.
    # This mirrors the AI service fallback. Narrowing to httpx.HTTPError could let
    # unexpected errors (e.g. serialisation) escape and break the pipeline.
    try:
        response = httpx.post(url, json=payload, timeout=_TELEGRAM_TIMEOUT_SECONDS)
        response.raise_for_status()
        logger.info("Telegram notification sent")
        return True
    except Exception as exc:
        logger.warning("Telegram notification failed (%s); skipping", type(exc).__name__)
        return False
