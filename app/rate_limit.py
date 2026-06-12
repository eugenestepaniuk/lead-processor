"""Rate limiter instance — kept in its own module to avoid circular imports.

Note: slowapi uses an in-memory store by default, which is fine for a single-process
deployment. For multi-process/multi-worker deployments a shared store (e.g. Redis) would
be needed — out of scope for this MVP.
"""

from __future__ import annotations

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

