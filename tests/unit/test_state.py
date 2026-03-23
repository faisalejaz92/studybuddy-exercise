"""Unit tests for state, config, and tools.

Unit tests are fast, deterministic, and don't require LLM calls.
"""

from graph.state import StudyBuddyState, FlashcardSession
from graph.config import ExperimentConfig
from graph.tools.notes import search_notes, generate_flashcards_with_state


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
    """generate_flashcards should return formatted questions only, no answers in questions, no JSON."""
    result, session = generate_flashcards_with_state({"query": "machine learning", "action": "create", "max_cards": 2}, None)

    # Should be formatted text, not JSON
    assert isinstance(result, str)
    assert "Here are 2 flashcards" in result
    assert "What is" in result or "What are" in result
    # Should not contain answers in the questions
    assert "Training with labeled data" not in result  # answer should not be in question text
    assert "{" not in result  # no JSON
    assert "}" not in result
    assert "[" not in result
    assert "]" not in result

    # Session should be created
    assert session is not None
    assert session["source_topic"] == "machine learning"
    assert len(session["all_generated_cards"]) > 0
    assert len(session["shown_card_ids"]) == 2  # served 2
    assert session["last_served_card_ids"]  # has the ids
    assert not session["answers_revealed"]


def test_generate_flashcards_handles_no_results():
    """generate_flashcards should gracefully handle no matching notes."""
    result, session = generate_flashcards_with_state({"query": "quantum physics", "action": "create", "max_cards": 5}, None)
    assert "No notes found" in result
    assert session is None


def test_generate_flashcards_more_unseen():
    """generate_flashcards should return only unseen cards for 'more' action, formatted."""
    # First create some cards
    _, session = generate_flashcards_with_state({"query": "machine learning", "action": "create", "max_cards": 1}, None)
    initial_shown = len(session["shown_card_ids"])

    # Then get more
    result, updated_session = generate_flashcards_with_state({"query": "machine learning", "action": "more", "max_cards": 2}, session)

    # Should be formatted text
    assert isinstance(result, str)
    assert "flashcards" in result
    assert "{" not in result  # no JSON
    # Check session updated
    assert len(updated_session["shown_card_ids"]) > initial_shown


def test_generate_flashcards_answers_reveal():
    """generate_flashcards should reveal answers for last served batch, formatted text."""
    # Create cards first
    _, session = generate_flashcards_with_state({"query": "machine learning", "action": "create", "max_cards": 2}, None)

    # Reveal answers
    result, updated_session = generate_flashcards_with_state({"action": "answers"}, session)

    # Should be formatted text
    assert isinstance(result, str)
    assert "Here are the answers" in result
    assert "Training with labeled data" in result  # answer should be present
    assert "{" not in result  # no JSON
    assert updated_session["answers_revealed"]


def test_generate_flashcards_answers_no_session():
    """generate_flashcards should handle answers request with no active session."""
    result, session = generate_flashcards_with_state({"action": "answers"}, None)
    assert "No active flashcards" in result
    assert session is None


def test_generate_flashcards_no_answer_leakage():
    """generate_flashcards should not include answers in question text."""
    result, _ = generate_flashcards_with_state({"query": "machine learning", "action": "create", "max_cards": 5}, None)

    # Check that answers are not embedded in questions
    assert "Training with labeled data" not in result
    assert "Finding patterns in unlabeled data" not in result
    assert "Learning through trial and error with rewards" not in result


def test_generate_flashcards_no_json_leakage():
    """generate_flashcards should return formatted text, not JSON."""
    result, _ = generate_flashcards_with_state({"query": "machine learning", "action": "create", "max_cards": 2}, None)

    assert isinstance(result, str)
    # Should not contain JSON markers
    assert "{" not in result
    assert "}" not in result
    assert "[" not in result
    assert "]" not in result
    assert '"question"' not in result
    assert '"answer"' not in result
