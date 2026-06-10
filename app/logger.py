"""Logging setup — configures the root logger once from application settings.

Usage:
    Call setup_logging() once at application startup (e.g. in main.py).
    Obtain named loggers anywhere via get_logger(__name__).
"""

from __future__ import annotations

import logging
import sys

from app.config import get_settings

# Idempotency guard — prevents duplicate handler registration on repeated calls.
_CONFIGURED: bool = False


def setup_logging() -> None:
    """Configure the root logger with a stdout StreamHandler.

    Level is taken from settings.log_level (never from os.environ directly).
    Safe to call multiple times — subsequent calls are no-ops.
    """
    global _CONFIGURED  # noqa: PLW0603
    if _CONFIGURED:
        return

    settings = get_settings()

    # Resolve numeric level; fall back to INFO for unknown/garbage values.
    level_name = settings.log_level.upper()
    level = getattr(logging, level_name, logging.INFO)
    if not isinstance(level, int):
        level = logging.INFO

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )

    root = logging.getLogger()
    root.setLevel(level)
    root.handlers.clear()  # avoid duplicate handlers on re-config
    root.addHandler(handler)

    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    """Return a named logger.

    Args:
        name: Logger name, typically ``__name__`` of the calling module.

    Returns:
        A :class:`logging.Logger` instance.
    """
    return logging.getLogger(name)

