"""Compiled graph for LangGraph server.

This file separates the compiled graph from build_graph().
Tests can import build_graph() from main.py without triggering
model initialization - only the LangGraph server imports this file.

langgraph.json references: ./graph/server.py:graph
"""

import os
from graph.main import build_graph

# Default model - override via LLM_MODEL env var
DEFAULT_MODEL = "gpt-4o"

MODEL = os.environ.get("LLM_MODEL", DEFAULT_MODEL)

# Build model kwargs from env vars (empty/unset values are omitted)
model_kwargs = {}

_temperature = os.environ.get("LLM_TEMPERATURE", "0.7")
if _temperature not in ("", "none"):
    model_kwargs["temperature"] = float(_temperature)

_reasoning_effort = os.environ.get("LLM_REASONING_EFFORT", "")
if _reasoning_effort:
    model_kwargs["reasoning_effort"] = _reasoning_effort

graph = build_graph(model=MODEL, model_kwargs=model_kwargs)
