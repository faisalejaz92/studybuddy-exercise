"""Eval tests for agent behavior with real LLM.

Eval tests verify the agent behaves correctly with real LLM calls.
They are slower and require API keys, so they're skipped by default.

Run with: make test-eval
"""

import os
import pytest
from langchain_core.messages import HumanMessage

pytestmark = pytest.mark.eval

# Use same model resolution as graph/server.py
DEFAULT_MODEL = "gpt-4o"


@pytest.fixture
def graph():
    """Build graph with real LLM (env must be loaded first)."""
    from graph.main import build_graph
    model = os.environ.get("LLM_MODEL", DEFAULT_MODEL)

    # Build model kwargs from env (same logic as server.py)
    model_kwargs = {}
    _temperature = os.environ.get("LLM_TEMPERATURE", "0.7")
    if _temperature not in ("", "none"):
        model_kwargs["temperature"] = float(_temperature)
    _reasoning_effort = os.environ.get("LLM_REASONING_EFFORT", "")
    if _reasoning_effort:
        model_kwargs["reasoning_effort"] = _reasoning_effort

    return build_graph(model=model, model_kwargs=model_kwargs)


def test_agent_responds_to_greeting(graph):
    """Agent should respond appropriately to a greeting."""
    result = graph.invoke({
        "messages": [HumanMessage(content="Hello!")]
    })

    response = result["messages"][-1].content
    assert len(response) > 0, "Agent should produce a non-empty response"
