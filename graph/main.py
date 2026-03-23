"""StudyBuddy experiment graph.

This module defines build_graph() but does NOT instantiate the graph at module
level. The compiled graph lives in server.py, which langgraph.json references.
"""

from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import SystemMessage, ToolMessage
from langgraph.graph import StateGraph, END
from langchain_core.tools import tool

from graph.config import ExperimentConfig
from graph.prompts.system import format_system_prompt
from graph.tools import generate_flashcards, generate_flashcards_with_state, search_notes
from graph.state import StudyBuddyState, FlashcardSession


def build_graph(model: str | BaseChatModel, model_kwargs: dict | None = None):
    """Build the StudyBuddy graph.

    Args:
        model: Model to use. Required. Can be:
            - A model string: "gpt-4o", "azure_openai:deployment", etc.
            - A BaseChatModel instance (for testing with mocks)
        model_kwargs: Optional kwargs passed to init_chat_model (e.g., temperature,
            reasoning_effort). Ignored when model is a BaseChatModel instance.

    Structure:
        Custom StateGraph with agent and tool nodes for stateful flashcard management.
    """
    print("Building StudyBuddy graph...")

    # Initialize model (supports injection for testing)
    if isinstance(model, str):
        print(f"Initializing model: {model}")
        model = init_chat_model(model, **(model_kwargs or {}))

    # Define tools
    tools = [search_notes, generate_flashcards]
    print(f"Loaded {len(tools)} tools: {[t.name for t in tools]}")

    # Bind tools to model
    model = model.bind_tools(tools)

    # System prompt
    system_prompt = format_system_prompt()

    def agent_node(state: StudyBuddyState) -> dict:
        """Agent node: calls LLM with current messages and tools."""
        messages = [SystemMessage(content=system_prompt)] + state["messages"]
        response = model.invoke(messages)
        return {"messages": [response]}

    def tool_node(state: StudyBuddyState) -> dict:
        """Tool node: executes tool calls and updates state as needed."""
        last_message = state["messages"][-1]
        if not hasattr(last_message, 'tool_calls') or not last_message.tool_calls:
            return {}

        # Process first tool call (assume single for simplicity)
        tool_call = last_message.tool_calls[0]
        tool_name = tool_call['name']
        tool_args = tool_call['args']

        if tool_name == 'search_notes':
            result = search_notes.invoke(tool_args)
            tool_message = ToolMessage(content=result, tool_call_id=tool_call['id'])
            return {"messages": [tool_message]}

        elif tool_name == 'generate_flashcards':
            # Stateful tool: updates flashcard_session
            result, updated_session = generate_flashcards_with_state(
                tool_args, state.get('flashcard_session')
            )
            tool_message = ToolMessage(content=result, tool_call_id=tool_call['id'])
            return {"messages": [tool_message], "flashcard_session": updated_session}

        return {}

    def should_continue(state: StudyBuddyState) -> str:
        """Determine next step: tools if tool calls present, else end."""
        last_message = state["messages"][-1]
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            return "tools"
        return END

    # Build custom graph
    graph = StateGraph(StudyBuddyState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", tool_node)
    graph.add_conditional_edges("agent", should_continue)
    graph.set_entry_point("agent")

    compiled_graph = graph.compile()
    print("StudyBuddy graph built successfully")
    return compiled_graph


