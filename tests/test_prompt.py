"""Unit tests for app/services/prompt.py — Block 3, subtask 3.2.

Pure, deterministic, offline — no GEMINI_API_KEY required.
"""

from __future__ import annotations

from app.schemas.lead import LeadIn
from app.services.prompt import build_summary_prompt


def test_build_summary_prompt_all_fields() -> None:
    """Prompt must contain every provided field value and the instruction keyword."""
    lead = LeadIn(
        name="Olena",
        email="olena@example.com",
        phone="+380501112233",
        message="Цікавить інтеграція CRM",
        source="landing",
    )
    prompt = build_summary_prompt(lead)

    assert isinstance(prompt, str)
    assert len(prompt) > 0

    # All field values must appear verbatim.
    assert "Olena" in prompt
    assert "olena@example.com" in prompt
    assert "+380501112233" in prompt
    assert "Цікавить інтеграція CRM" in prompt
    assert "landing" in prompt

    # Instruction keyword must be present.
    assert "Summarize" in prompt


def test_build_summary_prompt_minimal_lead() -> None:
    """Only provided fields appear; absent fields must not leak labels into the prompt."""
    lead = LeadIn(name="Ivan", email="ivan@example.com")

    prompt = build_summary_prompt(lead)

    assert "Ivan" in prompt
    assert "ivan@example.com" in prompt

    # Labels for omitted fields must not appear.
    assert "Phone:" not in prompt
    assert "Message:" not in prompt

