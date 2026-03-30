"""Custom Starlette app mounted into the LangGraph server.

Declared in langgraph.json as:
    { "http": { "app": "graph.http:app" } }

LangGraph merges this app's routes directly into its own Starlette router,
so all endpoints here are available on the same port as the LangGraph API
(default: http://localhost:2024).

Endpoints
---------
GET /logs
    Returns stored log entries as JSON. Supports the following query params:

    level       Filter by log level name (case-insensitive).
                e.g. ?level=ERROR  or  ?level=WARNING
    logger      Prefix-match on logger name.
                e.g. ?logger=graph.tools
    request_id  Exact match on request_id correlation field.
    event       Case-insensitive substring match on the event field.
    since       ISO-8601 timestamp — return only entries after this time.
                e.g. ?since=2026-03-30T12:00:00Z
    limit       Max entries to return (default 200, max 2000).

    Results are returned oldest-first.
"""

import json
from datetime import datetime, timezone

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Route

from graph.utils.log_store import get_all


# ---------------------------------------------------------------------------
# Request handler
# ---------------------------------------------------------------------------

async def logs_endpoint(request: Request) -> Response:
    """Return filtered log entries as a JSON array."""
    params = request.query_params

    # -- Parse filters -------------------------------------------------------
    level_filter    = (params.get("level") or "").strip().upper() or None
    logger_filter   = (params.get("logger") or "").strip() or None
    request_id      = (params.get("request_id") or "").strip() or None
    event_substr    = (params.get("event") or "").strip().lower() or None

    since_raw = (params.get("since") or "").strip()
    since_dt: datetime | None = None
    if since_raw:
        try:
            since_dt = datetime.fromisoformat(since_raw.replace("Z", "+00:00"))
        except ValueError:
            return Response(
                content=json.dumps({"error": f"Invalid 'since' timestamp: {since_raw!r}"}),
                status_code=400,
                media_type="application/json",
            )

    try:
        limit = min(int(params.get("limit", 200)), 2000)
    except ValueError:
        limit = 200

    # -- Filter entries ------------------------------------------------------
    entries = get_all()

    if level_filter:
        entries = [e for e in entries if e.get("level", "").upper() == level_filter]

    if logger_filter:
        entries = [e for e in entries if e.get("logger", "").startswith(logger_filter)]

    if request_id:
        entries = [e for e in entries if e.get("request_id") == request_id]

    if event_substr:
        entries = [e for e in entries if event_substr in e.get("event", "").lower()]

    if since_dt:
        def _after(entry: dict) -> bool:
            ts = entry.get("timestamp", "")
            try:
                return datetime.fromisoformat(ts) > since_dt
            except (ValueError, TypeError):
                return False
        entries = [e for e in entries if _after(e)]

    # Return newest-first so the UI can show most-recent at top without sorting
    entries = list(reversed(entries))[:limit]

    return Response(
        content=json.dumps({"entries": entries, "total": len(entries)}),
        media_type="application/json",
        headers={
            # Allow the Next.js dev server at :3000 to call this endpoint
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        },
    )


async def logs_options(request: Request) -> Response:
    """Handle CORS preflight for /logs."""
    return Response(
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        }
    )


# ---------------------------------------------------------------------------
# App — LangGraph merges these routes into its own router
# ---------------------------------------------------------------------------

app = Starlette(
    routes=[
        Route("/logs", endpoint=logs_endpoint, methods=["GET"]),
        Route("/logs", endpoint=logs_options, methods=["OPTIONS"]),
    ]
)
