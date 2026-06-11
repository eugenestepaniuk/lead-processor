"""Pytest configuration: set environment variables before any app module is imported."""

from __future__ import annotations

import os

# Disable optional integrations so Settings validation passes without real secrets.
os.environ.setdefault("AI_ENABLED", "false")
os.environ.setdefault("TELEGRAM_ENABLED", "false")

