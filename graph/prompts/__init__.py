"""Prompts for studybuddy experiment.

Re-exports from submodules. Keep this file minimal - put actual prompts in
separate files (e.g., system.py, tutor.py) following personalized_tutor pattern.
"""

from graph.prompts.system import SYSTEM_PROMPT, format_system_prompt

__all__ = ["SYSTEM_PROMPT", "format_system_prompt"]
