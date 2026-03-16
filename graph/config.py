"""Configuration for StudyBuddy."""

from dataclasses import dataclass, field


@dataclass(kw_only=True)
class ExperimentConfig:
    """Runtime configuration for StudyBuddy.

    Appears in LangGraph Studio's configuration sidebar.
    """

    user_id: str = field(
        default="anonymous",
        metadata={"description": "User identifier for the session"},
    )
