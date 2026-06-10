"""Smoke test: confirms pytest is configured and the `app` package is importable.

Placeholder scaffolding for subtask 0.3. It may be removed once real test modules
(test_lead_schema.py, etc.) exist, or kept as a sanity check.
"""

import app


def test_app_package_importable() -> None:
    assert app is not None
