"""Unit tests for state, config, and tools.

Unit tests are fast, deterministic, and don't require LLM calls.
"""

from graph.state import StudyBuddyState
from graph.config import ExperimentConfig
from graph.tools.notes import generate_flashcards, search_notes


def test_state_includes_messages():
    """StudyBuddyState should have messages from MessagesState."""
    state = StudyBuddyState(messages=[])
    assert "messages" in state
    assert state["messages"] == []


def test_config_has_user_id():
    """ExperimentConfig should have user_id with default."""
    config = ExperimentConfig()
    assert config.user_id == "anonymous"


def test_search_notes_finds_matching_content():
    """search_notes should find notes matching the query."""
    result = search_notes.invoke({"query": "machine learning"})
    assert "Machine learning" in result
    assert "supervised learning" in result.lower()


def test_search_notes_returns_message_when_not_found():
    """search_notes should return helpful message when no matches."""
    result = search_notes.invoke({"query": "quantum physics"})
    assert "No notes found" in result


def test_search_notes_searches_multiple_fields():
    """search_notes should search title, content, subject, and tags."""
    # Search by subject
    result = search_notes.invoke({"query": "biology"})
    assert "Photosynthesis" in result or "Cell Structure" in result

    # Search by tag
    result = search_notes.invoke({"query": "algebra"})
    assert "Quadratic" in result


def test_generate_flashcards_returns_cards():
    """generate_flashcards should return structured flashcards for known topics."""
    result = generate_flashcards.invoke({"query": "machine learning", "max_cards": 3})

    import json

    cards = json.loads(result)
    assert isinstance(cards, list)
    assert 1 <= len(cards) <= 3
    assert "question" in cards[0]
    assert "answer" in cards[0]
    assert "topic" in cards[0]


def test_generate_flashcards_handles_no_results():
    """generate_flashcards should gracefully handle no matching notes."""
    result = generate_flashcards.invoke({"query": "quantum physics", "max_cards": 5})
    assert "No notes found" in result
