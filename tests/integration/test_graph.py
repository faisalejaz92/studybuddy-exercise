"""Integration tests for graph wiring with mocked LLM.

Integration tests verify graph structure and state transitions
without making real LLM calls. Use FakeToolCallingModel to script
predictable responses.

Note: We import build_graph from main.py (not server.py) and pass a mock model.
This avoids init_chat_model() which requires API keys. See graph/__init__.py.
"""

from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

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
    assert "action=" in prompt
    assert "create" in prompt
    assert "answers" in prompt


def test_flashcard_create_then_answers():
    """Test create flashcards then reveal answers workflow."""
    # Mock model that calls generate_flashcards with create, then answers
    create_response = AIMessage(
        content="I'll create flashcards for you.",
        tool_calls=[{
            "id": "call_1",
            "name": "generate_flashcards",
            "args": {"query": "machine learning", "action": "create", "max_cards": 2}
        }]
    )
    answers_response = AIMessage(
        content="Here are the answers.",
        tool_calls=[{
            "id": "call_2",
            "name": "generate_flashcards",
            "args": {"action": "answers"}
        }]
    )

    mock_model = FakeToolCallingModel(responses=[create_response, answers_response])
    graph = build_graph(model=mock_model)

    # First interaction: create flashcards
    result1 = graph.invoke({
        "messages": [HumanMessage(content="Make flashcards for machine learning")]
    })

    # Should have tool call and response
    assert len(result1["messages"]) >= 3  # human, ai, tool
    assert isinstance(result1["messages"][-1], ToolMessage)

    # Check flashcard session was created
    assert result1.get("flashcard_session") is not None
    session = result1["flashcard_session"]
    assert session["source_topic"] == "machine learning"
    assert len(session["shown_card_ids"]) > 0

    # Second interaction: get answers
    result2 = graph.invoke(result1)

    # Should have answers
    assert len(result2["messages"]) >= 5  # previous + ai + tool
    assert isinstance(result2["messages"][-1], ToolMessage)
    tool_content = result2["messages"][-1].content
    assert "Here are the answers" in tool_content
    assert "Training with labeled data" in tool_content  # actual answer
    assert "{" not in tool_content  # no JSON leakage


def test_flashcard_create_then_more():
    """Test create flashcards then get more workflow."""
    create_response = AIMessage(
        content="Creating flashcards.",
        tool_calls=[{
            "id": "call_1",
            "name": "generate_flashcards",
            "args": {"query": "machine learning", "action": "create", "max_cards": 1}
        }]
    )
    more_response = AIMessage(
        content="Getting more cards.",
        tool_calls=[{
            "id": "call_2",
            "name": "generate_flashcards",
            "args": {"query": "machine learning", "action": "more", "max_cards": 2}
        }]
    )

    mock_model = FakeToolCallingModel(responses=[create_response, more_response])
    graph = build_graph(model=mock_model)

    # Create initial cards
    result1 = graph.invoke({
        "messages": [HumanMessage(content="Make flashcards for machine learning")]
    })

    initial_shown = len(result1["flashcard_session"]["shown_card_ids"])

    # Get more cards
    result2 = graph.invoke(result1)

    # Should have more cards shown
    final_shown = len(result2["flashcard_session"]["shown_card_ids"])
    assert final_shown > initial_shown

    # Check tool message is formatted text, not JSON
    tool_content = result2["messages"][-1].content
    assert "flashcards" in tool_content
    assert "{" not in tool_content  # no JSON


def test_flashcard_no_json_leakage():
    """Flashcard tool messages should be formatted text, not JSON."""
    create_response = AIMessage(
        content="Creating flashcards.",
        tool_calls=[{
            "id": "call_1",
            "name": "generate_flashcards",
            "args": {"query": "machine learning", "action": "create", "max_cards": 2}
        }]
    )

    mock_model = FakeToolCallingModel(responses=[create_response])
    graph = build_graph(model=mock_model)

    result = graph.invoke({
        "messages": [HumanMessage(content="Make flashcards for machine learning")]
    })

    # Check tool message content
    tool_message = None
    for msg in result["messages"]:
        if isinstance(msg, ToolMessage):
            tool_message = msg
            break

    assert tool_message is not None
    content = tool_message.content
    assert isinstance(content, str)
    assert "Here are" in content
    assert "What is" in content
    # No JSON
    assert "{" not in content
    assert "}" not in content
    assert "[" not in content
    assert "]" not in content


def test_flashcard_no_answer_leakage():
    """Flashcard questions should not contain answers."""
    create_response = AIMessage(
        content="Creating flashcards.",
        tool_calls=[{
            "id": "call_1",
            "name": "generate_flashcards",
            "args": {"query": "machine learning", "action": "create", "max_cards": 5}
        }]
    )

    mock_model = FakeToolCallingModel(responses=[create_response])
    graph = build_graph(model=mock_model)

    result = graph.invoke({
        "messages": [HumanMessage(content="Make flashcards for machine learning")]
    })

    # Check tool message content
    tool_message = None
    for msg in result["messages"]:
        if isinstance(msg, ToolMessage):
            tool_message = msg
            break

    assert tool_message is not None
    content = tool_message.content
    # Answers should not be in the question text
    assert "Training with labeled data" not in content
    assert "Finding patterns in unlabeled data" not in content
    assert "Learning through trial and error with rewards" not in content
