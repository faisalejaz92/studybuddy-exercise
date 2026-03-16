"""StudyBuddy experiment graph.

This module defines build_graph() but does NOT instantiate the graph at module
level. The compiled graph lives in server.py, which langgraph.json references.
"""

from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import SystemMessage
from langgraph.prebuilt import create_react_agent

from graph.config import ExperimentConfig
from graph.prompts.system import format_system_prompt
from graph.tools import search_notes


def build_graph(model: str | BaseChatModel, model_kwargs: dict | None = None):
    """Build the StudyBuddy graph.

    Args:
        model: Model to use. Required. Can be:
            - A model string: "gpt-4o", "azure_openai:deployment", etc.
            - A BaseChatModel instance (for testing with mocks)
        model_kwargs: Optional kwargs passed to init_chat_model (e.g., temperature,
            reasoning_effort). Ignored when model is a BaseChatModel instance.

    Structure:
        Uses create_react_agent with search_notes tool.
    """
    print("Building StudyBuddy graph...")

    # Initialize model (supports injection for testing)
    if isinstance(model, str):
        print(f"Initializing model: {model}")
        model = init_chat_model(model, **(model_kwargs or {}))

    # Define tools
    tools = [search_notes]
    print(f"Loaded {len(tools)} tools: {[t.name for t in tools]}")

    # System prompt
    system_prompt = format_system_prompt()

    # Build using create_react_agent for simple tool-calling agent
    graph = create_react_agent(
        model=model,
        tools=tools,
        prompt=SystemMessage(content=system_prompt),
        context_schema=ExperimentConfig,
    )

    print("StudyBuddy graph built successfully")
    return graph


