"""AI summary service — wraps the Google Gemini API (google-genai SDK).

Block 3, subtask 3.3: explicit request timeout + hardened fallback path.
"""

from __future__ import annotations

import logging
from functools import lru_cache

from google import genai
from google.genai import types

from app.config import get_settings
from app.schemas.lead import LeadIn
from app.services.prompt import build_summary_prompt

logger = logging.getLogger(__name__)

# Timeout passed to the google-genai HTTP layer (milliseconds).
# NOTE: the client-level HttpOptions timeout is documented but has known cases
# where the underlying httpx request may not honour it.  The broad except +
# None fallback below is the real guarantee that an AI failure never crashes
# the pipeline.  A hard wall-clock timeout (async client + asyncio.wait_for)
# would be a future hardening step, outside MVP scope.
_AI_REQUEST_TIMEOUT_MS = 15_000  # 15 s, best-effort client-level timeout


@lru_cache(maxsize=1)
def _get_client() -> genai.Client:
    """Return a cached Gemini client.

    Config fail-fast (see app/config.py _check_required_secrets) guarantees
    that gemini_api_key is present whenever ai_enabled is True, so no
    additional key check is needed here.
    """
    settings = get_settings()
    return genai.Client(
        api_key=settings.gemini_api_key,
        http_options=types.HttpOptions(timeout=_AI_REQUEST_TIMEOUT_MS),
    )


def generate_summary(lead: LeadIn) -> str | None:
    """Generate a short plain-text AI summary for the given lead.

    Returns:
        A non-empty summary string on success, or None when AI is disabled /
        the API call fails.  Never raises.
    """
    settings = get_settings()

    if not settings.ai_enabled:
        logger.debug("AI disabled; skipping summary")
        return None

    prompt = build_summary_prompt(lead)

    try:
        client = _get_client()
        response = client.models.generate_content(
            model=settings.ai_model,
            contents=prompt,
        )
        text = (response.text or "").strip()
        return text or None
    except Exception as exc:  # noqa: BLE001
        # Log only the exception type — never the lead or any PII.
        logger.warning("AI summary failed (%s); falling back to no summary", type(exc).__name__)
        return None



