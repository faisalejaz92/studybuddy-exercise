"""Unit tests for the generate_flashcards tool.

Tests are fast and deterministic — the internal LLM call (_call_llm_for_flashcards)
is mocked so no real API calls are made.
"""

from unittest.mock import MagicMock, patch

import pytest

from graph.tools.flashcards import (
    AVAILABLE_TOPICS,
    _find_matching_notes,
    generate_flashcards,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SAMPLE_FLASHCARDS = [
    {"question": "What is supervised learning?", "answer": "Training with labeled data."},
    {"question": "What is reinforcement learning?", "answer": "Learning through trial and error with rewards."},
    {"question": "Name a common ML algorithm.", "answer": "Decision trees."},
]


def _mock_llm(flashcards: list[dict]):
    """Return a patch target that makes _call_llm_for_flashcards return flashcards."""
    return patch(
        "graph.tools.flashcards._call_llm_for_flashcards",
        return_value=flashcards,
    )


# ---------------------------------------------------------------------------
# _find_matching_notes (pure function, no mocking needed)
# ---------------------------------------------------------------------------


def test_find_matching_notes_by_title():
    results = _find_matching_notes("machine learning")
    assert len(results) == 1
    assert results[0]["title"] == "Introduction to Machine Learning"


def test_find_matching_notes_by_subject():
    results = _find_matching_notes("biology")
    titles = [n["title"] for n in results]
    assert "Photosynthesis Process" in titles
    assert "Cell Structure and Organelles" in titles


def test_find_matching_notes_by_tag():
    results = _find_matching_notes("algebra")
    assert any("Quadratic" in n["title"] for n in results)


def test_find_matching_notes_no_match():
    results = _find_matching_notes("quantum physics")
    assert results == []


# ---------------------------------------------------------------------------
# generate_flashcards — unknown topic
# ---------------------------------------------------------------------------


def test_generate_flashcards_unknown_topic():
    result = generate_flashcards.invoke({"topic": "quantum physics"})
    assert "No notes found" in result
    assert AVAILABLE_TOPICS in result


# ---------------------------------------------------------------------------
# generate_flashcards — happy path
# ---------------------------------------------------------------------------


def test_generate_flashcards_returns_questions():
    with _mock_llm(SAMPLE_FLASHCARDS):
        result = generate_flashcards.invoke({"topic": "machine learning", "count": 3})

    assert "Q1." in result
    assert "Q2." in result
    assert "Q3." in result
    assert "What is supervised learning?" in result


def test_generate_flashcards_includes_answers_for_agent():
    """Answers must be present in tool output so the agent can reveal them on request."""
    with _mock_llm(SAMPLE_FLASHCARDS):
        result = generate_flashcards.invoke({"topic": "machine learning", "count": 3})

    assert "A1." in result
    assert "Training with labeled data." in result


def test_generate_flashcards_answers_section_is_labelled():
    """Output must clearly separate questions from answers."""
    with _mock_llm(SAMPLE_FLASHCARDS):
        result = generate_flashcards.invoke({"topic": "machine learning", "count": 3})

    assert "QUESTIONS" in result
    assert "ANSWERS" in result


def test_generate_flashcards_count_capped_at_10():
    """Requesting more than 10 cards should cap at 10."""
    with _mock_llm(SAMPLE_FLASHCARDS) as mock_fn:
        generate_flashcards.invoke({"topic": "machine learning", "count": 50})
        _, kwargs = mock_fn.call_args
        # count argument passed to _call_llm_for_flashcards must be ≤ 10
        called_count = mock_fn.call_args[0][1]  # positional: (notes_text, count)
        assert called_count <= 10


def test_generate_flashcards_count_minimum_is_1():
    """Requesting 0 or negative cards should floor at 1."""
    with _mock_llm(SAMPLE_FLASHCARDS) as mock_fn:
        generate_flashcards.invoke({"topic": "machine learning", "count": 0})
        called_count = mock_fn.call_args[0][1]
        assert called_count >= 1


# ---------------------------------------------------------------------------
# generate_flashcards — error handling
# ---------------------------------------------------------------------------


def test_generate_flashcards_handles_json_parse_error():
    import json

    with patch(
        "graph.tools.flashcards._call_llm_for_flashcards",
        side_effect=json.JSONDecodeError("bad json", "", 0),
    ):
        result = generate_flashcards.invoke({"topic": "machine learning"})

    assert "Could not parse" in result


def test_generate_flashcards_handles_llm_exception():
    with patch(
        "graph.tools.flashcards._call_llm_for_flashcards",
        side_effect=RuntimeError("LLM unavailable"),
    ):
        result = generate_flashcards.invoke({"topic": "machine learning"})

    assert "Error generating flashcards" in result


def test_generate_flashcards_handles_empty_llm_response():
    with _mock_llm([]):
        result = generate_flashcards.invoke({"topic": "machine learning"})

    assert "Could not generate" in result


# ---------------------------------------------------------------------------
# generate_flashcards — content grounding
# ---------------------------------------------------------------------------


def test_generate_flashcards_passes_notes_to_llm():
    """The LLM must receive the actual note content, not an empty string."""
    with patch(
        "graph.tools.flashcards._call_llm_for_flashcards",
        return_value=SAMPLE_FLASHCARDS,
    ) as mock_fn:
        generate_flashcards.invoke({"topic": "machine learning"})
        notes_text_arg = mock_fn.call_args[0][0]

    assert "Machine learning" in notes_text_arg
    assert "supervised learning" in notes_text_arg.lower()


def test_generate_flashcards_does_not_pass_unrelated_notes():
    """Only matching notes should be sent to the LLM."""
    with patch(
        "graph.tools.flashcards._call_llm_for_flashcards",
        return_value=SAMPLE_FLASHCARDS,
    ) as mock_fn:
        generate_flashcards.invoke({"topic": "photosynthesis"})
        notes_text_arg = mock_fn.call_args[0][0]

    assert "Photosynthesis" in notes_text_arg
    assert "Quadratic" not in notes_text_arg
    assert "French Revolution" not in notes_text_arg
