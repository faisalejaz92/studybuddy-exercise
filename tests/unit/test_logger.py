"""Unit tests for graph/utils/logger.py.

All tests are fast and deterministic — no LLM calls, no network I/O.
"""

import json
import logging
from io import StringIO

import pytest

from graph.utils.logger import get_logger, request_id_var


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _capture_logs(logger_name: str = "test.logger") -> tuple[logging.Logger, StringIO]:
    """Return a (logger, buffer) pair where log output is captured in buffer.

    Installs a temporary StreamHandler with the JSON formatter so we can
    assert on the emitted JSON without touching stdout.
    """
    from graph.utils.logger import _JsonFormatter

    buf = StringIO()
    handler = logging.StreamHandler(buf)
    handler.setFormatter(_JsonFormatter())

    logger = logging.getLogger(logger_name)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    # Prevent propagation so we don't also write to the root handler during tests
    logger.propagate = False

    return logger, buf


def _parse_last_line(buf: StringIO) -> dict:
    """Return the last non-empty JSON line from buf."""
    lines = [l for l in buf.getvalue().strip().splitlines() if l.strip()]
    assert lines, "No log lines were emitted"
    return json.loads(lines[-1])


# ---------------------------------------------------------------------------
# JSON structure
# ---------------------------------------------------------------------------

def test_log_line_is_valid_json():
    logger, buf = _capture_logs("test.json")
    logger.info("hello world")
    record = _parse_last_line(buf)
    assert isinstance(record, dict)


def test_log_line_has_required_fields():
    logger, buf = _capture_logs("test.fields")
    logger.info("some event")
    record = _parse_last_line(buf)

    assert "timestamp" in record
    assert "level" in record
    assert "logger" in record
    assert "event" in record


def test_event_field_matches_message():
    logger, buf = _capture_logs("test.event")
    logger.info("tool.search_notes.start")
    record = _parse_last_line(buf)
    assert record["event"] == "tool.search_notes.start"


def test_level_field_matches_severity():
    logger, buf = _capture_logs("test.level")
    logger.warning("watch out")
    record = _parse_last_line(buf)
    assert record["level"] == "WARNING"


def test_logger_field_matches_name():
    logger, buf = _capture_logs("test.mymodule")
    logger.info("x")
    record = _parse_last_line(buf)
    assert record["logger"] == "test.mymodule"


# ---------------------------------------------------------------------------
# Extra fields
# ---------------------------------------------------------------------------

def test_extra_fields_are_merged_into_output():
    logger, buf = _capture_logs("test.extra")
    logger.info("tool.start", extra={"tool_name": "search_notes", "duration_ms": 42})
    record = _parse_last_line(buf)
    assert record["tool_name"] == "search_notes"
    assert record["duration_ms"] == 42


def test_multiple_extra_fields():
    logger, buf = _capture_logs("test.multi_extra")
    logger.info(
        "agent.turn.start",
        extra={"status": "start", "user_id": "u-123", "thread_id": "t-456"},
    )
    record = _parse_last_line(buf)
    assert record["status"] == "start"
    assert record["user_id"] == "u-123"
    assert record["thread_id"] == "t-456"


# ---------------------------------------------------------------------------
# request_id propagation
# ---------------------------------------------------------------------------

def test_request_id_absent_when_not_set():
    """No request_id field when the ContextVar is empty."""
    token = request_id_var.set("")
    try:
        logger, buf = _capture_logs("test.no_rid")
        logger.info("event")
        record = _parse_last_line(buf)
        assert "request_id" not in record
    finally:
        request_id_var.reset(token)


def test_request_id_included_when_set():
    token = request_id_var.set("run-abc-123")
    try:
        logger, buf = _capture_logs("test.with_rid")
        logger.info("event")
        record = _parse_last_line(buf)
        assert record["request_id"] == "run-abc-123"
    finally:
        request_id_var.reset(token)


def test_request_id_reset_after_context_exits():
    """Resetting the ContextVar removes request_id from subsequent logs."""
    token = request_id_var.set("run-xyz")
    request_id_var.reset(token)

    logger, buf = _capture_logs("test.rid_reset")
    logger.info("after reset")
    record = _parse_last_line(buf)
    assert "request_id" not in record


# ---------------------------------------------------------------------------
# Error / exception handling
# ---------------------------------------------------------------------------

def test_exception_info_is_included_as_string():
    logger, buf = _capture_logs("test.exc")
    try:
        raise ValueError("something went wrong")
    except ValueError:
        logger.error("tool.error", exc_info=True)

    record = _parse_last_line(buf)
    assert "error" in record
    assert "ValueError" in record["error"]
    assert "something went wrong" in record["error"]


def test_exception_does_not_produce_multiline_output():
    """Each log record must be a single JSON line — no multi-line tracebacks."""
    logger, buf = _capture_logs("test.exc_oneline")
    try:
        raise RuntimeError("boom")
    except RuntimeError:
        logger.error("fail", exc_info=True)

    lines = [l for l in buf.getvalue().strip().splitlines() if l.strip()]
    # Every line must be valid JSON (i.e., no raw traceback lines leaked)
    for line in lines:
        json.loads(line)  # raises if not valid JSON


# ---------------------------------------------------------------------------
# get_logger
# ---------------------------------------------------------------------------

def test_get_logger_returns_logger_instance():
    lg = get_logger("test.factory")
    assert isinstance(lg, logging.Logger)


def test_get_logger_same_name_returns_same_instance():
    a = get_logger("test.dedup")
    b = get_logger("test.dedup")
    assert a is b
