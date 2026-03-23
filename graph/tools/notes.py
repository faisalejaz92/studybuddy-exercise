"""Notes search tool for StudyBuddy.

This tool searches through the user's study notes and returns relevant content.
"""

from langchain_core.tools import tool
import hashlib
import json
from typing import Dict, Any, List, Optional, Tuple

# Sample notes data - in a real app this would come from a database
SAMPLE_NOTES = [
    {
        "id": 1,
        "title": "Introduction to Machine Learning",
        "content": """Machine learning is a subset of artificial intelligence that enables
systems to learn and improve from experience without being explicitly programmed.
Key concepts include:
- Supervised learning: Training with labeled data
- Unsupervised learning: Finding patterns in unlabeled data
- Reinforcement learning: Learning through trial and error with rewards
Common algorithms: Linear regression, decision trees, neural networks, SVMs.""",
        "subject": "Computer Science",
        "tags": ["ML", "AI", "algorithms"],
    },
    {
        "id": 2,
        "title": "The French Revolution",
        "content": """The French Revolution (1789-1799) was a period of radical political
and societal change in France. Key events:
- 1789: Storming of the Bastille (July 14)
- 1789: Declaration of the Rights of Man
- 1793-1794: Reign of Terror under Robespierre
- 1799: Napoleon's coup d'état
Causes included financial crisis, social inequality, and Enlightenment ideas.""",
        "subject": "History",
        "tags": ["revolution", "France", "18th century"],
    },
    {
        "id": 3,
        "title": "Photosynthesis Process",
        "content": """Photosynthesis is the process by which plants convert light energy
into chemical energy. The equation:
6CO2 + 6H2O + light energy → C6H12O6 + 6O2

Two main stages:
1. Light-dependent reactions (in thylakoids): Capture light, split water, produce ATP
2. Calvin cycle (in stroma): Use ATP to fix CO2 into glucose

Chlorophyll absorbs red and blue light, reflects green.""",
        "subject": "Biology",
        "tags": ["plants", "energy", "chemistry"],
    },
    {
        "id": 4,
        "title": "Quadratic Equations",
        "content": """A quadratic equation has the form ax² + bx + c = 0 where a ≠ 0.

Solutions using the quadratic formula:
x = (-b ± √(b² - 4ac)) / 2a

The discriminant (b² - 4ac) determines the nature of roots:
- Positive: Two distinct real roots
- Zero: One repeated real root
- Negative: Two complex conjugate roots

Factoring and completing the square are alternative solving methods.""",
        "subject": "Mathematics",
        "tags": ["algebra", "equations", "polynomials"],
    },
    {
        "id": 5,
        "title": "Cell Structure and Organelles",
        "content": """Eukaryotic cells contain membrane-bound organelles:

- Nucleus: Contains DNA, controls cell activities
- Mitochondria: Powerhouse of the cell, produces ATP
- Endoplasmic reticulum: Rough (ribosomes) for protein synthesis, smooth for lipids
- Golgi apparatus: Packages and ships proteins
- Lysosomes: Digest waste materials
- Cell membrane: Controls what enters and exits

Prokaryotic cells (bacteria) lack membrane-bound organelles.""",
        "subject": "Biology",
        "tags": ["cells", "organelles", "anatomy"],
    },
]


def _find_matching_notes(query: str):
    """Return notes that match the query using the same logic as search_notes."""
    query_lower = query.lower()
    matching_notes = []

    for note in SAMPLE_NOTES:
        searchable = (
            note["title"].lower()
            + " "
            + note["content"].lower()
            + " "
            + note["subject"].lower()
            + " "
            + " ".join(note["tags"]).lower()
        )

        if any(word in searchable for word in query_lower.split()):
            matching_notes.append(note)

    return matching_notes


def _extract_fact_items(note):
    """Extract lines from content that look like facts to make flashcards."""
    lines = []
    for raw_line in note["content"].splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("-") or line.startswith("*") or line[0].isdigit():
            lines.append(line.lstrip("-*0123456789. ").strip())

    # fallback to first sentence(s)
    if not lines:
        first_paragraph = note["content"].split("\n\n")[0].strip()
        for sentence in first_paragraph.split("."):
            sentence = sentence.strip()
            if sentence:
                lines.append(sentence)
                if len(lines) >= 5:  # Allow more facts for larger pool
                    break

    return lines


def _parse_fact(fact: str) -> Optional[Tuple[str, str]]:
    """Parse a fact string into question and answer.

    Expects format like "Term: Definition" or "1. Term: Definition"
    Returns (question, answer) or None if malformed.
    """
    fact = fact.strip()
    if not fact:
        return None

    # Remove leading numbers/bullets
    fact = fact.lstrip("0123456789. -*")

    if ":" not in fact:
        # If no colon, treat as answer and generate generic question
        return f"What is this?", fact

    parts = fact.split(":", 1)
    if len(parts) != 2:
        return None

    term = parts[0].strip()
    definition = parts[1].strip()

    if not term or not definition:
        return None

    # Generate question
    # Simple heuristic: if term contains plural words, use "What are", else "What is"
    plural_indicators = ["reactions", "processes", "equations", "structures", "organelles", "algorithms"]
    if any(indicator in term.lower() for indicator in plural_indicators):
        question = f"What are {term}?"
    else:
        question = f"What is {term}?"

    return question, definition


def _generate_candidate_cards(query: str) -> List[Dict[str, Any]]:
    """Generate all possible flashcards from matching notes."""
    matching_notes = _find_matching_notes(query)
    if not matching_notes:
        return []

    cards = []
    for note in matching_notes:
        fact_items = _extract_fact_items(note)
        for fact in fact_items:
            parsed = _parse_fact(fact)
            if parsed:
                question, answer = parsed
                topic = note["title"]
                card_id = hashlib.md5(f"{question}{answer}{topic}".encode()).hexdigest()
                cards.append({
                    "id": card_id,
                    "question": question,
                    "answer": answer,
                    "topic": topic
                })

    return cards


def generate_flashcards_with_state(args: Dict[str, Any], current_session: Optional[Dict[str, Any]]) -> Tuple[str, Optional[Dict[str, Any]]]:
    """Stateful flashcard generation with create/more/answers actions.

    Returns (result_string, updated_session)
    """
    query = args.get("query", "")
    action = args.get("action", "create")
    max_cards = args.get("max_cards", 5)

    print(f"generate_flashcards_with_state called with query: {query}, action: {action}, max_cards={max_cards}")

    # Handle answers action first (doesn't need query)
    if action == "answers":
        if not current_session or not current_session.get("last_served_card_ids"):
            return "No active flashcards to reveal answers for. Try creating flashcards first.", current_session

        if current_session.get("answers_revealed", False):
            # Re-reveal answers
            pass
        else:
            current_session["answers_revealed"] = True

        last_served_ids = current_session["last_served_card_ids"]
        answers = []
        for card in current_session["all_generated_cards"]:
            if card["id"] in last_served_ids:
                answers.append(card)

        if not answers:
            return "No answers found for the current flashcards.", current_session

        answers_text = "\n".join(f"{i+1}. {answer['answer']}" for i, answer in enumerate(answers))
        message = f"Here are the answers for your flashcards:\n\n{answers_text}"
        return message, current_session

    # For create/more actions, need query
    if not query:
        return "Please specify a topic for flashcards.", current_session

    # Check if we need to reset session (new topic)
    if not current_session or current_session.get("source_topic") != query:
        current_session = {
            "source_topic": query,
            "all_generated_cards": [],
            "shown_card_ids": [],
            "last_served_card_ids": [],
            "answers_revealed": False
        }

    # Generate candidate cards if not already done
    if not current_session["all_generated_cards"]:
        current_session["all_generated_cards"] = _generate_candidate_cards(query)
        print(f"Generated {len(current_session['all_generated_cards'])} candidate cards")

    if not current_session["all_generated_cards"]:
        return "No notes found matching your query. Can't generate flashcards right now.", None

    # Get unseen cards
    shown_ids = set(current_session["shown_card_ids"])
    unseen_cards = [c for c in current_session["all_generated_cards"] if c["id"] not in shown_ids]

    if not unseen_cards:
        total_cards = len(current_session["all_generated_cards"])
        return f"I've already shown you all {total_cards} unique flashcards from your notes on this topic.", current_session

    # Serve up to max_cards
    to_serve = unseen_cards[:max_cards]
    served_ids = [c["id"] for c in to_serve]

    # Update session
    current_session["shown_card_ids"].extend(served_ids)
    current_session["last_served_card_ids"] = served_ids
    current_session["answers_revealed"] = False

    # Prepare result
    if not to_serve:
        return "No more flashcards available for this topic.", current_session

    cards_text = "\n".join(f"{i+1}. {card['question']}" for i, card in enumerate(to_serve))
    message = f"Here are {len(to_serve)} flashcards for {query}:\n\n{cards_text}"
    if len(to_serve) < max_cards:
        remaining = len(unseen_cards) - len(to_serve)
        if remaining == 0:
            message += "\n\n(That's all the unique flashcards available for this topic.)"
        else:
            message += f"\n\n({remaining} more available. Say 'generate more flashcards' to see them.)"
    else:
        message += "\n\n(Use 'give me answers' to see the answers, or 'generate more flashcards' for additional ones.)"

    print(f"Served {len(to_serve)} cards, {len(unseen_cards) - len(to_serve)} remaining")
    return message, current_session


@tool
def search_notes(query: str) -> str:
    """Search through study notes to find relevant information.

    Args:
        query: The search query - can be a topic, keyword, or question.

    Returns:
        Relevant notes content or a message if nothing found.
    """
    print(f"search_notes called with query: {query}")

    matching_notes = _find_matching_notes(query)

    if not matching_notes:
        print("  No matches found")
        return "No notes found matching your query. Try different keywords or check if you have notes on this topic."

    # Format results
    results = []
    for note in matching_notes:
        results.append(
            f"## {note['title']}\n**Subject:** {note['subject']}\n\n{note['content']}"
        )

    print(f"  Returning {len(matching_notes)} notes")
    return "\n\n---\n\n".join(results)


@tool
def generate_flashcards(query: str, action: str = "create", max_cards: int = 5) -> str:
    """Generate or manage flashcards from study notes.

    Actions:
    - "create": Generate initial flashcards for a topic (questions only)
    - "more": Generate additional unseen flashcards
    - "answers": Reveal answers for the most recently served flashcards

    Args:
        query: Topic or search query (required for create/more)
        action: Action to perform ("create", "more", "answers")
        max_cards: Maximum cards to generate (for create/more)

    Returns:
        JSON response with flashcards or answers, or error message.
    """
    # This tool is now handled statefully in the graph
    # The actual logic is in generate_flashcards_with_state
    return "Tool called directly - use through graph for state management."
