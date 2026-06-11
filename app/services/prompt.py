"""Prompt builders for the AI summary service.

Pure, deterministic functions — no network, no settings, no I/O.
Block 3, subtask 3.2: summary prompt only.
Block 4, subtask 4.2: combined analysis prompt (summary + classification).
"""

from __future__ import annotations

from app.schemas.ai_result import CATEGORY_CRITERIA
from app.schemas.lead import LeadIn

_SUMMARY_INSTRUCTION = (
    "You are a sales assistant. Summarize the following inbound lead in 1-2 concise sentences "
    "for the sales team. State who the lead is, how to reach them, and what they want. "
    "Be strictly factual — do not invent any detail that is not present in the data. "
    "Respond in the same language as the lead's message; "
    "if the language is unclear, respond in Ukrainian."
)

# Rubric shown to the model for classification (excludes the "unknown" system fallback).
_CLASSIFICATION_RUBRIC = "\n".join(
    f'- "{category}": {criterion}'
    for category, criterion in CATEGORY_CRITERIA.items()
    if category != "unknown"
)


def _build_lead_data_block(lead: LeadIn) -> str:
    """Return a 'Lead data:' text block containing only non-None fields."""
    lines: list[str] = [f"Name: {lead.name}"]

    if lead.email is not None:
        lines.append(f"Email: {lead.email}")
    if lead.phone is not None:
        lines.append(f"Phone: {lead.phone}")
    if lead.message is not None:
        lines.append(f"Message: {lead.message}")
    if lead.source is not None:
        lines.append(f"Source: {lead.source}")

    return "Lead data:\n" + "\n".join(lines)


def build_summary_prompt(lead: LeadIn) -> str:
    """Return a complete prompt string for the Gemini summary call.

    Only fields that are not None are included in the lead-data block.
    Name is always present (it is a required field on LeadIn).

    Args:
        lead: The validated inbound lead.

    Returns:
        A plain-text prompt ready to pass to the model.
    """
    return f"{_SUMMARY_INSTRUCTION}\n\n{_build_lead_data_block(lead)}"


def build_analysis_prompt(lead: LeadIn) -> str:
    """Return a prompt that asks the model for a summary AND classification in one call.

    The model must respond with ONLY a JSON object — no markdown fences, no prose.
    Expected keys: summary (str), category ("hot"|"warm"|"cold"), reason (str).

    Args:
        lead: The validated inbound lead.

    Returns:
        A plain-text prompt ready to pass to the model.
    """
    instruction = (
        "You are a sales assistant. Analyse the following inbound lead and respond with "
        "ONLY a JSON object — no markdown, no code fences, no prose outside the JSON.\n\n"
        "The JSON must have EXACTLY these keys:\n"
        '  {"summary": "...", "category": "hot|warm|cold", "reason": "..."}\n\n'
        "Rules:\n"
        "1. summary: 1-2 concise, factual sentences for the sales team — who the lead is, "
        "how to reach them, and what they want. Be strictly factual — do not invent any "
        "detail not present in the data. Respond in the same language as the lead's message; "
        "if the language is unclear, respond in Ukrainian.\n"
        "2. category: classify the lead as EXACTLY ONE of: hot, warm, cold "
        "(NEVER use 'unknown'). Use the following rubric:\n"
        f"{_CLASSIFICATION_RUBRIC}\n"
        "3. reason: one short sentence justifying the chosen category.\n\n"
        "Respond with the JSON object only."
    )
    return f"{instruction}\n\n{_build_lead_data_block(lead)}"
