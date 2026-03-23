"""Notes search tool for StudyBuddy.

This tool searches through the user's study notes and returns relevant content.
"""

from langchain_core.tools import tool

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
                if len(lines) >= 3:
                    break

    return lines


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
def generate_flashcards(query: str, max_cards: int = 5) -> str:
    """Generate 3-5 structured flashcards grounded in retrieved notes.

    Returns a JSON array of flashcards with keys:
      question, answer, optional topic

    If notes are insufficient, the tool responds gracefully.
    """
    print(f"generate_flashcards called with query: {query}, max_cards={max_cards}")

    matching_notes = _find_matching_notes(query)
    if not matching_notes:
        msg = "No notes found matching your query. Can't generate flashcards right now."
        print(f"  {msg}")
        return msg

    cards = []
    for note in matching_notes:
        fact_items = _extract_fact_items(note)
        if not fact_items:
            continue

        for fact in fact_items:
            if len(cards) >= max_cards:
                break
            question = f"What is: {fact}?"
            answer = fact
            cards.append({"question": question, "answer": answer, "topic": note["title"]})

        if len(cards) >= max_cards:
            break

    if not cards:
        msg = "Found notes but could not extract good flashcards. Try a different query."
        print(f"  {msg}")
        return msg

    if len(cards) < 3:
        note_names = ", ".join([n["title"] for n in matching_notes])
        print(f"  Only {len(cards)} cards generated from notes: {note_names}")

    import json

    result = json.dumps(cards, indent=2, ensure_ascii=False)
    print(f"  Generated {len(cards)} flashcards")
    return result
