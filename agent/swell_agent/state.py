"""Core state model for a swell interview session.

See the root README.md's Task 2 "Core state model" - this mirrors that JSON
shape as a LangGraph state schema. One graph run processes one incoming
event; LangGraph Platform's checkpointer carries this state across separate
runs on the same thread (session_id == thread_id).
"""

from __future__ import annotations

from typing import Annotated, Literal, Optional, TypedDict

from langgraph.graph.message import add_messages

MilestoneStatus = Literal["NOT_STARTED", "PARTIAL", "IN_PROGRESS", "COMPLETED"]
CandidateStatus = Literal["PROGRESSING", "POSSIBLY_STUCK", "DEBUGGING_DIFFICULTY"]
RecommendedAction = Literal["ask", "hint", "wait"]

EventType = Literal[
    "CANDIDATE_MESSAGE",
    "CODE_SNAPSHOT",
    "CANDIDATE_IDLE",
    "CODE_RUN_COMPLETED",
    "HINT_REQUESTED",
]

# Matches knowledge-base/two-sum/milestones.yaml's milestone ids.
MILESTONE_IDS = [
    "UNDERSTANDS_PROBLEM",
    "CLARIFIES_CONSTRAINTS",
    "PROPOSES_APPROACH",
    "PROPOSES_HASH_MAP",
    "STATES_COMPLEXITY",
    "HANDLES_EDGE_CASES",
    "IMPLEMENTS_CORRECT_SOLUTION",
]


class MilestoneRecord(TypedDict):
    status: MilestoneStatus
    confidence: float
    evidence_event_ids: list[str]


def initial_milestones() -> dict[str, MilestoneRecord]:
    return {
        milestone_id: MilestoneRecord(
            status="NOT_STARTED", confidence=0.0, evidence_event_ids=[]
        )
        for milestone_id in MILESTONE_IDS
    }


class InterviewEvent(TypedDict):
    event_id: str
    type: EventType
    payload: dict


class InterviewState(TypedDict):
    session_id: str
    problem_id: str
    status: Literal["IN_PROGRESS", "COMPLETED"]
    current_phase: str
    candidate_status: CandidateStatus
    milestones: dict[str, MilestoneRecord]
    hint_level: int
    failed_run_count: int
    latest_code_snapshot_id: Optional[str]
    messages: Annotated[list, add_messages]

    # Per-turn scratch fields, overwritten each run rather than persisted history.
    incoming_event: InterviewEvent
    pending_evaluation: Optional[dict]
    recommended_action: Optional[RecommendedAction]


def new_session_defaults() -> dict:
    """Fields to seed on a session's first-ever event.

    normalize_event applies these when milestones is missing/empty, rather than
    requiring a separate "create session" step before the first real event.
    """
    return {
        "status": "IN_PROGRESS",
        "current_phase": "PROBLEM_INTRO",
        "candidate_status": "PROGRESSING",
        "milestones": initial_milestones(),
        "hint_level": 0,
        "failed_run_count": 0,
        "latest_code_snapshot_id": None,
    }
