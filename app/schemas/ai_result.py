"""Single source of truth for the lead classification taxonomy.

Categories and their selection criteria are defined here so that every other
module (prompt builder, result parser, tests) imports from this file.

``"unknown"`` is a NON-selectable system fallback — the AI model must never
choose it; it is injected programmatically when the AI is disabled, unavailable,
or returns an invalid response.
"""

from __future__ import annotations

from typing import Final, Literal, TypeAlias

from pydantic import BaseModel, ConfigDict

# ---------------------------------------------------------------------------
# Taxonomy
# ---------------------------------------------------------------------------

LeadCategory: TypeAlias = Literal["hot", "warm", "cold", "unknown"]

CATEGORY_CRITERIA: Final[dict[LeadCategory, str]] = {
    "hot": (
        "Strong, immediate buying intent — explicit request to buy / get pricing / "
        "book a demo or call, a stated budget or timeline, or a ready-to-proceed "
        "decision maker."
    ),
    "warm": (
        "Genuine interest without commitment — asking about the product/service, "
        "comparing options, or requesting more info, with no urgency or purchase signal."
    ),
    "cold": (
        "Weak, vague, or unclear intent — generic message, just browsing, off-topic, "
        "or likely spam/irrelevant."
    ),
    "unknown": (
        "System fallback only — used when AI is disabled/unavailable or returns an "
        "invalid response; the model never selects this category itself."
    ),
}


# ---------------------------------------------------------------------------
# Result model  (added in 4.2)
# ---------------------------------------------------------------------------


class AIResult(BaseModel):
    """Parsed response from a single Gemini analysis call."""

    model_config = ConfigDict(extra="ignore")  # ignore unexpected keys from the model

    summary: str | None = None
    category: LeadCategory  # REQUIRED; model emits hot/warm/cold only
    reason: str | None = None


