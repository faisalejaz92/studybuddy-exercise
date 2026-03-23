"""State schema for StudyBuddy.

Note: This file exists for future expansion. The current graph uses
create_react_agent which manages its own state internally.
"""

from langgraph.graph import MessagesState
from typing import Optional, List, Dict, Any


class FlashcardSession:
    """Session state for flashcard generation and management."""

    source_topic: str
    all_generated_cards: List[Dict[str, Any]]  # List of {"id": str, "question": str, "answer": str, "topic": str}
    shown_card_ids: List[str]  # IDs of cards already shown to user
    last_served_card_ids: List[str]  # IDs of last batch served (for answer reveal)
    answers_revealed: bool  # Whether answers have been revealed for last_served_card_ids


class StudyBuddyState(MessagesState):
    """State for the StudyBuddy graph.

    Extends MessagesState which provides:
    - messages: list of chat messages with add_messages reducer

    Add experiment-specific state fields here as needed.
    """

    flashcard_session: Optional[Dict[str, Any]] = None
