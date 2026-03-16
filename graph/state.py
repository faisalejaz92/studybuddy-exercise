"""State schema for StudyBuddy.

Note: This file exists for future expansion. The current graph uses
create_react_agent which manages its own state internally.
"""

from langgraph.graph import MessagesState


class StudyBuddyState(MessagesState):
    """State for the StudyBuddy graph.

    Extends MessagesState which provides:
    - messages: list of chat messages with add_messages reducer

    Add experiment-specific state fields here as needed.
    """

    pass
