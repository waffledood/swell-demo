"""Simulates a short multi-turn interview locally, to sanity-check the graph
without needing `langgraph dev` or a real deployment. Uses an in-memory
checkpointer just for this script - the exported `graph` in graph.py has none,
since LangGraph Platform supplies its own at deploy time.
"""

from __future__ import annotations

from dotenv import load_dotenv
from langgraph.checkpoint.memory import InMemorySaver

from swell_agent.graph import build_graph
from swell_agent.text import extract_text

load_dotenv()

EVENTS = [
    {
        "type": "CANDIDATE_MESSAGE",
        "payload": {
            "text": (
                "Hi, I think I need to find two numbers in the array that add up "
                "to a target value, and return their indices."
            )
        },
    },
    {
        "type": "CANDIDATE_MESSAGE",
        "payload": {"text": "Can the array have duplicate values?"},
    },
    {
        "type": "CANDIDATE_MESSAGE",
        "payload": {"text": "I'll use a hash map to store seen values as I go."},
    },
    {"type": "HINT_REQUESTED", "payload": {}},
]


def main() -> None:
    graph = build_graph(checkpointer=InMemorySaver())
    config = {"configurable": {"thread_id": "try-graph-session"}}

    result = None
    for i, event in enumerate(EVENTS):
        full_event = {**event, "event_id": f"evt-{i}"}
        print(f"\n=== Turn {i}: {full_event['type']} - {full_event['payload']} ===")
        result = graph.invoke({"incoming_event": full_event}, config=config)

        print("recommended_action:", result["recommended_action"])
        print("candidate_status:", result["candidate_status"])

        last_message = result["messages"][-1] if result["messages"] else None
        if last_message is not None and last_message.__class__.__name__ == "AIMessage":
            print("coach:", extract_text(last_message))
        else:
            print("(no message sent this turn)")

    print("\n=== Final milestones ===")
    for milestone_id, record in result["milestones"].items():
        print(
            f"{milestone_id}: {record['status']} (confidence={record['confidence']})"
        )


if __name__ == "__main__":
    main()
