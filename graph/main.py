"""StudyBuddy experiment graph.

This module defines build_graph() but does NOT instantiate the graph at module
level. The compiled graph lives in server.py, which langgraph.json references.
"""

import time
import uuid
from typing import Any

from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.prebuilt import create_react_agent

from graph.config import ExperimentConfig
from graph.prompts.system import format_system_prompt
from graph.tools import generate_flashcards, search_notes
from graph.utils.logger import get_logger, request_id_var

log = get_logger(__name__)


def _make_correlation_hook():
    """Return a pre_model_hook that sets request_id for the duration of each turn.

    LangGraph calls this node before every LLM invocation in the ReAct loop.
    It receives the current graph state and the LangGraph RunnableConfig.

    We extract the run_id from config (set by LangGraph per invocation) and
    store it in the request_id ContextVar so every logger in this call-stack
    automatically includes it — no argument threading required.

    Returns:
        A callable compatible with create_react_agent's pre_model_hook.
    """
    def _hook(state: Any, config: RunnableConfig) -> dict:
        # Use LangGraph's run_id as our request_id for full correlation.
        # Fall back to a fresh UUID if (somehow) the config has none.
        run_id = str(config.get("run_id") or uuid.uuid4())
        request_id_var.set(run_id)

        # Surface the user_id from configurable if available
        configurable = config.get("configurable") or {}
        user_id = configurable.get("user_id", "anonymous")
        thread_id = configurable.get("thread_id", "")

        log.info(
            "agent.turn.start",
            extra={
                "status": "start",
                "user_id": user_id,
                "thread_id": thread_id,
            },
        )
        # Return empty dict — we're not modifying graph state, only setting context
        return {}

    return _hook


def build_graph(model: str | BaseChatModel, model_kwargs: dict | None = None):
    """Build the StudyBuddy graph.

    Args:
        model: Model to use. Required. Can be:
            - A model string: "gpt-4o", "azure_openai:deployment", etc.
            - A BaseChatModel instance (for testing with mocks)
        model_kwargs: Optional kwargs passed to init_chat_model (e.g., temperature,
            reasoning_effort). Ignored when model is a BaseChatModel instance.

    Structure:
        Uses create_react_agent with search_notes and generate_flashcards tools.
        A pre_model_hook sets a per-turn request_id for log correlation.
    """
    log.info("graph.build.start")

    # Initialize model (supports injection for testing)
    if isinstance(model, str):
        log.info("graph.model.init", extra={"model": model})
        model = init_chat_model(model, **(model_kwargs or {}))

    # Define tools
    tools = [search_notes, generate_flashcards]
    log.info(
        "graph.tools.loaded",
        extra={"tool_names": [t.name for t in tools], "tool_count": len(tools)},
    )

    # System prompt
    system_prompt = format_system_prompt()

    # Build using create_react_agent — the LLM selects tools based on intent.
    # Tool docstrings and the system prompt are the routing mechanism; no
    # programmatic keyword matching is needed or used.
    #
    # pre_model_hook runs before every LLM call and sets the request_id
    # ContextVar so all tool logs in the same turn share the same ID.
    graph = create_react_agent(
        model=model,
        tools=tools,
        prompt=SystemMessage(content=system_prompt),
        context_schema=ExperimentConfig,
        pre_model_hook=_make_correlation_hook(),
    )

    log.info("graph.build.complete")
    return graph
