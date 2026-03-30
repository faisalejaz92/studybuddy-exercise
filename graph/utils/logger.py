"""Structured JSON logging for StudyBuddy.

Usage
-----
    from graph.utils.logger import get_logger, request_id_var

    log = get_logger(__name__)
    log.info("tool.start", extra={"tool_name": "search_notes", "query": "ML"})

Every log record automatically includes:
  - timestamp (ISO-8601, UTC)
  - level
  - logger   (Python logger name)
  - request_id  (injected from the ambient ContextVar — set once per agent run)

Add any extra fields via the `extra` kwarg on the log call.

Design notes
------------
- Pure stdlib: no third-party deps.
- JSON lines to stdout: works with any log aggregator (CloudWatch, Datadog, etc.)
- ContextVar for request_id: propagates automatically across sync and async code
  that runs in the same context, without needing to thread it through call signatures.
- One-time configuration: calling get_logger() multiple times for the same name is
  safe — Python's logging module de-duplicates loggers by name.
"""

import json
import logging
import sys
import traceback
from contextvars import ContextVar
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Per-request correlation ID
# ---------------------------------------------------------------------------

# Set this once at the start of each agent run (see graph/main.py).
# All loggers read it automatically via the JSON formatter below.
request_id_var: ContextVar[str] = ContextVar("request_id", default="")


# ---------------------------------------------------------------------------
# JSON formatter
# ---------------------------------------------------------------------------

class _JsonFormatter(logging.Formatter):
    """Formats each log record as a single JSON line."""

    def format(self, record: logging.LogRecord) -> str:
        # Base fields present on every log line
        entry: dict = {
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "event": record.getMessage(),
        }

        # Inject ambient request_id (empty string → omit the field)
        rid = request_id_var.get()
        if rid:
            entry["request_id"] = rid

        # Merge any extra fields passed via log(..., extra={...})
        # Skip internal LogRecord attributes to avoid noise.
        _SKIP = {
            "name", "msg", "args", "levelname", "levelno", "pathname",
            "filename", "module", "exc_info", "exc_text", "stack_info",
            "lineno", "funcName", "created", "msecs", "relativeCreated",
            "thread", "threadName", "processName", "process", "message",
            "taskName",
        }
        for key, value in record.__dict__.items():
            if key not in _SKIP and not key.startswith("_"):
                entry[key] = value

        # Attach exception info as a structured field, not a multi-line string
        if record.exc_info:
            entry["error"] = "".join(traceback.format_exception(*record.exc_info)).strip()

        return json.dumps(entry, default=str)


# ---------------------------------------------------------------------------
# Configuration — called once when this module is first imported
# ---------------------------------------------------------------------------

def _configure_root_logger() -> None:
    """Attach JSON stdout handler and in-memory handler to the root logger."""
    import os  # noqa: PLC0415
    from graph.utils.log_store import MemoryLogHandler  # noqa: PLC0415

    root = logging.getLogger()

    # Avoid adding duplicate handlers if the module is somehow re-imported
    if any(isinstance(h, logging.StreamHandler) and
           isinstance(h.formatter, _JsonFormatter)
           for h in root.handlers):
        return

    # 1. Stdout handler — JSON lines for log aggregators / terminal
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(_JsonFormatter())
    root.addHandler(stdout_handler)

    # 2. In-memory handler — feeds the /logs API endpoint
    root.addHandler(MemoryLogHandler())

    # Default level: INFO. Override via LOG_LEVEL env var at startup if needed.
    level_name = os.environ.get("LOG_LEVEL", "INFO").upper()
    root.setLevel(getattr(logging, level_name, logging.INFO))


_configure_root_logger()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_logger(name: str) -> logging.Logger:
    """Return a named logger that emits structured JSON.

    Args:
        name: Typically __name__ of the calling module.

    Returns:
        A standard logging.Logger — use .debug / .info / .warning / .error.
        Pass structured fields via extra={"key": value}.
    """
    return logging.getLogger(name)
