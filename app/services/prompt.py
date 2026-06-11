"""Prompt builders for the AI summary service.

Pure, deterministic functions — no network, no settings, no I/O.
Block 3, subtask 3.2: summary prompt only.
Classification / structured-JSON prompts will be added in Block 4.
"""

from __future__ import annotations

from app.schemas.lead import LeadIn

_SUMMARY_INSTRUCTION = (
    "You are a sales assistant. Summarize the following inbound lead in 1-2 concise sentences "
    "for the sales team. State who the lead is, how to reach them, and what they want. "
    "Be strictly factual — do not invent any detail that is not present in the data. "
    "Respond in the same language as the lead's message; if the language is unclear, respond in Ukrainian."
)


def build_summary_prompt(lead: LeadIn) -> str:
    """Return a complete prompt string for the Gemini summary call.

    Only fields that are not None are included in the lead-data block.
    Name is always present (it is a required field on LeadIn).

    Args:
        lead: The validated inbound lead.

    Returns:
        A plain-text prompt ready to pass to the model.
    """
    lines: list[str] = [f"Name: {lead.name}"]

    if lead.email is not None:
        lines.append(f"Email: {lead.email}")
    if lead.phone is not None:
        lines.append(f"Phone: {lead.phone}")
    if lead.message is not None:
        lines.append(f"Message: {lead.message}")
    if lead.source is not None:
        lines.append(f"Source: {lead.source}")

    lead_block = "Lead data:\n" + "\n".join(lines)
    return f"{_SUMMARY_INSTRUCTION}\n\n{lead_block}"

