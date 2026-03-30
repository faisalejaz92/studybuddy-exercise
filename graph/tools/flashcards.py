"""Flashcard generation tool for StudyBuddy.

Generates Q&A flashcards from the student's study notes using an LLM.
The tool fetches relevant notes, then calls the LLM to extract structured
question/answer pairs strictly grounded in that content.
"""

import json
import os
import time

from langchain.chat_models import init_chat_model
from langchain_core.tools import tool

from graph.tools.notes import SAMPLE_NOTES
from graph.utils.logger import get_logger

log = get_logger(__name__)

AVAILABLE_TOPICS = (
    "Machine Learning, The French Revolution, Photosynthesis, "
    "Cell Structure, Quadratic Equations"
)

_FLASHCARD_PROMPT = """\
You are a study assistant. Generate exactly {count} flashcards from the notes below.
Use ONLY information present in the notes — do not add outside knowledge.

NOTES:
{notes_text}

Return a JSON array and nothing else:
[{{"question": "...", "answer": "..."}}]

Rules:
- Each question tests a specific fact, concept, or definition from the notes
- Each answer is short and factual (1-2 sentences maximum)
- Do not repeat the same question twice
- Do not include information not found in the notes above\
"""


def _find_matching_notes(topic: str) -> list[dict]:
    """Return notes whose title, content, subject, or tags contain any word from topic."""
    query_lower = topic.lower()
    matches = []
    for note in SAMPLE_NOTES:
        searchable = " ".join(
            [
                note["title"].lower(),
                note["content"].lower(),
                note["subject"].lower(),
                *[t.lower() for t in note["tags"]],
            ]
        )
        if any(word in searchable for word in query_lower.split()):
            matches.append(note)
    return matches


def _call_llm_for_flashcards(notes_text: str, count: int) -> list[dict]:
    """Call the configured LLM to extract Q&A pairs from notes_text.

    Separated from the tool so tests can mock this function cleanly.

    Returns:
        List of dicts with 'question' and 'answer' keys.

    Raises:
        json.JSONDecodeError: If the LLM response cannot be parsed as JSON.
        Exception: For any LLM call failure.
    """
    model_name = os.environ.get("LLM_MODEL", "gpt-4o")
    llm = init_chat_model(model_name, temperature=0.3)

    prompt = _FLASHCARD_PROMPT.format(count=count, notes_text=notes_text)
    response = llm.invoke(prompt)
    content = response.content.strip()

    # Strip markdown code fences if the LLM wrapped its response
    if content.startswith("```"):
        lines = content.splitlines()
        content = "\n".join(lines[1:-1]).strip()

    return json.loads(content)


@tool
def generate_flashcards(topic: str, count: int = 5) -> str:
    """Generate study flashcards when the student's intent is active recall or knowledge testing.

    Use this tool whenever the student's goal is to *test themselves* rather than
    *passively read*. This includes explicit requests ("quiz me", "make flashcards")
    and indirect ones ("help me remember this", "test my understanding",
    "give me practice questions", "what should I know?", "I want to review",
    "can you check if I understand this?"). Use judgment: if the student is trying
    to actively retrieve or verify knowledge — not just ask a question — use this tool.

    Do NOT use for plain factual questions like "what is photosynthesis?" — those
    should be answered directly or via search_notes.

    Questions are shown first; answers are embedded in the output and should only
    be revealed when the student explicitly asks for them.

    Args:
        topic: The subject or topic to generate flashcards for.
        count: Number of flashcards to generate (default 5, capped at 10).

    Returns:
        Numbered questions followed by answers for the agent to reveal on request.
    """
    start = time.monotonic()
    count = min(max(count, 1), 10)

    log.info(
        "tool.generate_flashcards.start",
        extra={
            "tool_name": "generate_flashcards",
            "status": "start",
            "topic": topic,
            "count_requested": count,
        },
    )

    matching_notes = _find_matching_notes(topic)
    if not matching_notes:
        duration_ms = round((time.monotonic() - start) * 1000, 1)
        log.info(
            "tool.generate_flashcards.complete",
            extra={
                "tool_name": "generate_flashcards",
                "status": "success",
                "topic": topic,
                "results_count": 0,
                "duration_ms": duration_ms,
            },
        )
        return (
            f"No notes found on '{topic}'. "
            f"Available topics: {AVAILABLE_TOPICS}."
        )

    notes_text = "\n\n".join(
        f"## {n['title']}\n{n['content']}" for n in matching_notes
    )
    log.info(
        "tool.generate_flashcards.llm_call",
        extra={
            "tool_name": "generate_flashcards",
            "notes_count": len(matching_notes),
            "count_requested": count,
        },
    )

    try:
        flashcards = _call_llm_for_flashcards(notes_text, count)
    except json.JSONDecodeError as exc:
        duration_ms = round((time.monotonic() - start) * 1000, 1)
        log.error(
            "tool.generate_flashcards.error",
            extra={
                "tool_name": "generate_flashcards",
                "status": "error",
                "error_type": "json_parse",
                "duration_ms": duration_ms,
            },
            exc_info=exc,
        )
        return "Could not parse flashcards from the LLM response. Please try again."
    except Exception as exc:
        duration_ms = round((time.monotonic() - start) * 1000, 1)
        log.error(
            "tool.generate_flashcards.error",
            extra={
                "tool_name": "generate_flashcards",
                "status": "error",
                "error_type": "llm_call",
                "duration_ms": duration_ms,
            },
            exc_info=exc,
        )
        return f"Error generating flashcards: {exc}"

    if not flashcards:
        duration_ms = round((time.monotonic() - start) * 1000, 1)
        log.warning(
            "tool.generate_flashcards.empty",
            extra={
                "tool_name": "generate_flashcards",
                "status": "success",
                "topic": topic,
                "results_count": 0,
                "duration_ms": duration_ms,
            },
        )
        return (
            f"Could not generate any flashcards for '{topic}' "
            "from the available notes. The topic may not have enough content."
        )

    duration_ms = round((time.monotonic() - start) * 1000, 1)
    log.info(
        "tool.generate_flashcards.complete",
        extra={
            "tool_name": "generate_flashcards",
            "status": "success",
            "topic": topic,
            "results_count": len(flashcards),
            "duration_ms": duration_ms,
        },
    )

    # Format output: questions first, answers below a divider.
    # The agent is instructed (via system prompt) to show only questions
    # and reveal answers only when the student asks.
    lines = [
        f"**Flashcards: {topic.title()}** — {len(flashcards)} card(s)\n",
        "QUESTIONS (show these to the student):",
    ]
    for i, card in enumerate(flashcards, 1):
        lines.append(f"  Q{i}. {card['question']}")

    lines.append("\nANSWERS (reveal only when the student asks):")
    for i, card in enumerate(flashcards, 1):
        lines.append(f"  A{i}. {card['answer']}")

    return "\n".join(lines)
