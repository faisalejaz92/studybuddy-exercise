"""Notes search tool for StudyBuddy.

This tool searches through the user's study notes and returns relevant content.
"""

import time

from langchain_core.tools import tool

from graph.utils.logger import get_logger

log = get_logger(__name__)

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


@tool
def search_notes(query: str) -> str:
    """Search through study notes to find relevant information.

    Args:
        query: The search query - can be a topic, keyword, or question.

    Returns:
        Relevant notes content or a message if nothing found.
    """
    start = time.monotonic()
    log.info(
        "tool.search_notes.start",
        extra={"tool_name": "search_notes", "status": "start"},
    )

    query_lower = query.lower()
    matching_notes = []

    for note in SAMPLE_NOTES:
        # Check title, content, subject, and tags
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

    duration_ms = round((time.monotonic() - start) * 1000, 1)

    if not matching_notes:
        log.info(
            "tool.search_notes.complete",
            extra={
                "tool_name": "search_notes",
                "status": "success",
                "results_count": 0,
                "duration_ms": duration_ms,
            },
        )
        return "No notes found matching your query. Try different keywords or check if you have notes on this topic."

    log.info(
        "tool.search_notes.complete",
        extra={
            "tool_name": "search_notes",
            "status": "success",
            "results_count": len(matching_notes),
            "matched_titles": [n["title"] for n in matching_notes],
            "duration_ms": duration_ms,
        },
    )

    # Format results
    results = []
    for note in matching_notes:
        results.append(
            f"## {note['title']}\n**Subject:** {note['subject']}\n\n{note['content']}"
        )

    return "\n\n---\n\n".join(results)
