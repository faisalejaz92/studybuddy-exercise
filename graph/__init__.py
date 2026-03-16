"""Graph module for studybuddy experiment.

Import directly from submodules:
    from graph.main import build_graph
    from graph.state import ExperimentState
    from graph.config import ExperimentConfig

Architecture:
    - main.py: build_graph() function only (no module-level graph)
    - server.py: graph = build_graph() for langgraph.json
    - langgraph.json references ./graph/server.py:graph

Why this separation? Tests can import build_graph() and call it with a mock
model, without triggering real model initialization. Only server.py (loaded
by LangGraph) calls build_graph() with the default (real) model.
"""
