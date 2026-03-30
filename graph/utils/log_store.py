"""In-memory log store for StudyBuddy.

Provides a thread-safe ring buffer that holds the most recent log records as
plain dicts, and a logging.Handler that feeds into it.

Design decisions
----------------
- collections.deque with maxlen: O(1) append, automatic eviction of the oldest
  entry, and thread-safe for appends/reads on CPython (GIL).
- Plain dicts, not LogRecord objects: serialisation happens once at emit time,
  so the query path is pure list filtering with no formatting overhead.
- Max 2000 entries: enough history for a 100-user beta without unbounded growth.
  At ~500 bytes/entry that's ~1 MB worst-case.
- Module-level singleton: any code that imports this module shares the same
  deque, including the Starlette HTTP endpoint in graph/http.py.
"""

import logging
import traceback
from collections import deque
from datetime import datetime, timezone
from typing import Any

# ---------------------------------------------------------------------------
# The store — one global deque, shared across all modules
# ---------------------------------------------------------------------------

MAX_ENTRIES = 2000

_store: deque[dict[str, Any]] = deque(maxlen=MAX_ENTRIES)


def get_all() -> list[dict[str, Any]]:
    """Return a snapshot of all stored log entries, oldest first."""
    return list(_store)


def clear() -> None:
    """Wipe the store (useful in tests)."""
    _store.clear()


# ---------------------------------------------------------------------------
# Internal LogRecord attribute names to drop from the stored dict.
# These are Python logging internals that add noise without value.
# ---------------------------------------------------------------------------

_SKIP = frozenset({
    "name", "msg", "args", "levelname", "levelno", "pathname",
    "filename", "module", "exc_info", "exc_text", "stack_info",
    "lineno", "funcName", "created", "msecs", "relativeCreated",
    "thread", "threadName", "processName", "process", "message",
    "taskName",
})


# ---------------------------------------------------------------------------
# Handler
# ---------------------------------------------------------------------------

class MemoryLogHandler(logging.Handler):
    """Converts LogRecords to plain dicts and appends them to _store."""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            # Import here to avoid a circular import (logger imports log_store,
            # log_store must not import logger at module level).
            from graph.utils.logger import request_id_var  # noqa: PLC0415

            entry: dict[str, Any] = {
                "timestamp": datetime.now(tz=timezone.utc).isoformat(),
                "level": record.levelname,
                "logger": record.name,
                "event": record.getMessage(),
            }

            rid = request_id_var.get()
            if rid:
                entry["request_id"] = rid

            # Merge extra fields set via log(..., extra={...})
            for key, value in record.__dict__.items():
                if key not in _SKIP and not key.startswith("_"):
                    entry[key] = value

            # Structured exception field
            if record.exc_info:
                entry["error"] = "".join(
                    traceback.format_exception(*record.exc_info)
                ).strip()

            _store.append(entry)
        except Exception:
            # Never crash the application due to a logging failure.
            self.handleError(record)
