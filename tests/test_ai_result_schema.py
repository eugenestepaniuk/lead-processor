"""Tests for the classification taxonomy defined in app/schemas/ai_result.py."""

from __future__ import annotations

from app.schemas.ai_result import CATEGORY_CRITERIA, AIResult

# ---------------------------------------------------------------------------
# 4.1 taxonomy tests (unchanged)
# ---------------------------------------------------------------------------

def test_category_criteria_keys() -> None:
    assert set(CATEGORY_CRITERIA) == {"hot", "warm", "cold", "unknown"}


def test_category_criteria_values_are_non_empty_strings() -> None:
    for category, criterion in CATEGORY_CRITERIA.items():
        assert isinstance(criterion, str), f"Value for {category!r} is not a str"
        assert criterion.strip() != "", f"Value for {category!r} is empty or whitespace"
        assert criterion == criterion.strip(), (
            f"Value for {category!r} has leading/trailing whitespace"
        )


def test_unknown_criterion_mentions_fallback() -> None:
    assert "fallback" in CATEGORY_CRITERIA["unknown"].lower()


# ---------------------------------------------------------------------------
# 4.2 AIResult model tests
# ---------------------------------------------------------------------------

def test_ai_result_valid_full_json() -> None:
    """Valid full JSON must parse into the correct AIResult fields."""
    result = AIResult.model_validate_json(
        '{"summary":"s","category":"hot","reason":"r"}'
    )
    assert result.summary == "s"
    assert result.category == "hot"
    assert result.reason == "r"


def test_ai_result_extra_keys_ignored() -> None:
    """Extra keys in the JSON must be silently ignored (extra='ignore')."""
    result = AIResult.model_validate_json(
        '{"summary":"s","category":"warm","reason":"r","foo":"bar"}'
    )
    assert result.summary == "s"
    assert result.category == "warm"
    assert not hasattr(result, "foo")


def test_ai_result_optional_fields_default_to_none() -> None:
    """summary and reason are optional; category is required."""
    result = AIResult.model_validate_json('{"category":"cold"}')
    assert result.category == "cold"
    assert result.summary is None
    assert result.reason is None


