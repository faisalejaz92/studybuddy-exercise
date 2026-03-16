"""Tests for studybuddy experiment.

Three-tier testing strategy:
- unit/        Fast, no LLM, test extracted logic
- integration/ Mocked LLM, test graph wiring
- evals/       Real LLM, test behavioral quality

See docs/langgraph-knowledge/project-conventions.md#three-tier-testing-strategy
"""
