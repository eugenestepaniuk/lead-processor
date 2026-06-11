"""AI analysis service — wraps the Google Gemini API (google-genai SDK).

Block 3, subtask 3.3: explicit request timeout + hardened fallback path.
Block 4, subtask 4.2: single Gemini call returns summary + classification as AIResult.
Block 4, subtask 4.3: invalid/unparseable model response falls back to category="unknown".
"""

from __future__ import annotations

import logging
import re
from functools import lru_cache

from google import genai
from google.genai import types
from pydantic import ValidationError

from app.config import get_settings
from app.schemas.ai_result import AIResult
from app.schemas.lead import LeadIn
from app.services.prompt import build_analysis_prompt

logger = logging.getLogger(__name__)

# Timeout passed to the google-genai HTTP layer (milliseconds).
# NOTE: the client-level HttpOptions timeout is documented but has known cases
# where the underlying httpx request may not honour it.  The broad except +
# None fallback below is the real guarantee that an AI failure never crashes
# the pipeline.  A hard wall-clock timeout (async client + asyncio.wait_for)
# would be a future hardening step, outside MVP scope.
_AI_REQUEST_TIMEOUT_MS = 15_000  # 15 s, best-effort client-level timeout

# Regex to strip optional ```json ... ``` or ``` ... ``` markdown fences.
_FENCE_RE = re.compile(r"^\s*```(?:json)?\s*(.*?)\s*```\s*$", re.DOTALL)


@lru_cache(maxsize=1)
def _get_client() -> genai.Client:
    """Return a cached Gemini client."""
    settings = get_settings()
    return genai.Client(
        api_key=settings.gemini_api_key,
        http_options=types.HttpOptions(timeout=_AI_REQUEST_TIMEOUT_MS),
    )


def _extract_json(text: str) -> str:
    """Strip surrounding whitespace and optional markdown code fences from *text*.

    Models often wrap JSON in ```json ... ``` even when instructed not to.
    Returns the inner JSON text ready for parsing.
    """
    text = text.strip()
    match = _FENCE_RE.match(text)
    return match.group(1).strip() if match else text


def analyze_lead(lead: LeadIn) -> AIResult | None:
    """Generate an AI analysis (summary + classification) for the given lead.

    Semantic contract:
    - None                     → AI disabled OR infrastructure failure (network, timeout,
                                 empty response text).
    - AIResult(category="unknown") → AI responded but the content is invalid/unusable
                                 (malformed JSON, missing category, or category outside
                                 hot/warm/cold).
    - AIResult(category=...)   → successful parse with a valid category.

    Never raises.
    """
    settings = get_settings()

    if not settings.ai_enabled:
        logger.debug("AI disabled; skipping analysis")
        return None

    prompt = build_analysis_prompt(lead)

    try:
        client = _get_client()
        response = client.models.generate_content(
            model=settings.ai_model,
            contents=prompt,
        )
        # Empty / missing response text is treated as an infrastructure failure.
        raw = (response.text or "").strip()
        if not raw:
            logger.warning("AI returned empty response text; falling back to no result")
            return None

        cleaned = _extract_json(raw)

        # Narrow guard: parse/validation errors mean the *content* is unusable,
        # not that the infrastructure failed — return unknown instead of None.
        try:
            return AIResult.model_validate_json(cleaned)
        except (ValidationError, ValueError) as exc:
            # Log only the exception type — never raw content or any PII.
            logger.warning(
                "AI response invalid (%s); classifying as 'unknown'",
                type(exc).__name__,
            )
            return AIResult(category="unknown", summary=None, reason=None)

    except Exception as exc:  # noqa: BLE001
        # Infrastructure / SDK / network failure — log type only, return None.
        logger.warning(
            "AI analysis failed (%s); falling back to no result",
            type(exc).__name__,
        )
        return None
