"""Structured output schema for the evaluate node's LLM call.

Kept separate from the graph's TypedDict state (state.py) - this is what the
LLM is asked to produce, not what's persisted turn-to-turn.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from swell_agent.state import CandidateStatus, MilestoneStatus, RecommendedAction


class MilestoneObservation(BaseModel):
    milestone_id: str = Field(description="One of the fixed milestone ids provided in context")
    status: MilestoneStatus
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: str = Field(
        description="One sentence citing what the candidate actually said/did"
    )


class EvaluationResult(BaseModel):
    observations: list[MilestoneObservation] = Field(
        description="Only include milestones with new evidence this turn - omit "
        "unchanged ones"
    )
    candidate_status: CandidateStatus
    recommended_action: RecommendedAction = Field(
        description="ask: pose a follow-up/clarifying question. hint: the "
        "candidate needs a nudge. wait: say nothing this turn (e.g. they're "
        "mid-thought or just ran code that failed and hasn't asked for help yet)"
    )
    reasoning: str = Field(
        description="Brief internal reasoning for the recommended_action - not "
        "shown to the candidate"
    )
