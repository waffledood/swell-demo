"""Builds the swell interview coaching graph.

build_graph() takes an optional checkpointer for local testing (e.g.
langgraph.checkpoint.memory.InMemorySaver). The module-level `graph` below is
compiled with no checkpointer - LangGraph Platform supplies its own
Postgres-backed one at deploy time (see CLAUDE.md's stack decisions).
"""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from swell_agent.nodes import (
    apply_deterministic_rules,
    evaluate,
    finish_check,
    generate_feedback,
    normalize_event,
    respond,
    route_action,
    route_finish,
    update_milestones,
)
from swell_agent.state import InterviewState


def build_graph(checkpointer=None):
    builder = StateGraph(InterviewState)

    builder.add_node("normalize_event", normalize_event)
    builder.add_node("apply_deterministic_rules", apply_deterministic_rules)
    builder.add_node("evaluate", evaluate)
    builder.add_node("update_milestones", update_milestones)
    builder.add_node("respond", respond)
    builder.add_node("finish_check", finish_check)
    builder.add_node("generate_feedback", generate_feedback)

    builder.add_edge(START, "normalize_event")
    builder.add_edge("normalize_event", "apply_deterministic_rules")
    builder.add_edge("apply_deterministic_rules", "evaluate")
    builder.add_edge("evaluate", "update_milestones")
    builder.add_conditional_edges(
        "update_milestones",
        route_action,
        {"respond": "respond", "finish_check": "finish_check"},
    )
    builder.add_edge("respond", "finish_check")
    builder.add_conditional_edges(
        "finish_check",
        route_finish,
        {"generate_feedback": "generate_feedback", "__end__": END},
    )
    builder.add_edge("generate_feedback", END)

    return builder.compile(checkpointer=checkpointer)


graph = build_graph()
