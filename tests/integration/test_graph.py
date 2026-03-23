"""Integration tests for graph wiring with mocked LLM.

Integration tests verify graph structure and state transitions
without making real LLM calls. Use FakeToolCallingModel to script
predictable responses.

Note: We import build_graph from main.py (not server.py) and pass a mock model.
This avoids init_chat_model() which requires API keys. See graph/__init__.py.
"""

from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage, HumanMessage

from graph.main import build_graph


class FakeToolCallingModel(FakeMessagesListChatModel):
    """FakeMessagesListChatModel that supports bind_tools.

    The standard FakeMessagesListChatModel doesn't implement bind_tools,
    which graphs with tools require. This subclass adds a no-op bind_tools
    since responses are pre-scripted.
    """

    def bind_tools(self, tools, **kwargs):
        """No-op bind_tools - returns self since responses are pre-scripted."""
        return self


def test_graph_compiles():
    """Graph should compile without errors (using mock model)."""
    mock_model = FakeToolCallingModel(responses=[
        AIMessage(content="Test response")
    ])
    graph = build_graph(model=mock_model)
    assert graph is not None


def test_graph_responds_to_message():
    """Graph should respond to a user message."""
    mock_model = FakeToolCallingModel(responses=[
        AIMessage(content="Hello! How can I help you today?")
    ])
    graph = build_graph(model=mock_model)

    result = graph.invoke({
        "messages": [HumanMessage(content="Hi")]
    })

    assert len(result["messages"]) == 2
    assert "Hello" in result["messages"][-1].content


def test_system_prompt_mentions_flashcards_tool():
    """System prompt should mention generate_flashcards as a study review option."""
    from graph.prompts.system import format_system_prompt

    prompt = format_system_prompt()
    assert "generate_flashcards" in prompt
    assert "quiz me" in prompt
