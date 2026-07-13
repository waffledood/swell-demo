"""The 6 graph nodes and their routing functions.

One graph run = one incoming event:
  normalize_event -> apply_deterministic_rules -> evaluate -> update_milestones
    -> route_action -> [respond ->] finish_check -> [generate_feedback ->] END
"""

from __future__ import annotations

from typing import Optional

from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage

from swell_agent.hints import get_next_hint
from swell_agent.milestones import render_milestone_criteria
from swell_agent.models import get_chat_model
from swell_agent.retriever import retrieve_problem_context
from swell_agent.schemas import EvaluationResult
from swell_agent.state import InterviewEvent, InterviewState, MilestoneRecord, new_session_defaults
from swell_agent.web_search import search_general_programming_concept

# ---------------------------------------------------------------------------
# normalize_event
# ---------------------------------------------------------------------------


def normalize_event(state: InterviewState) -> dict:
    updates: dict = {}
    if not state.get("milestones"):
        updates.update(new_session_defaults())

    event = state["incoming_event"]
    if event["type"] == "CANDIDATE_MESSAGE":
        updates["messages"] = [HumanMessage(content=event["payload"]["text"])]
    elif event["type"] == "CODE_SNAPSHOT":
        updates["latest_code_snapshot_id"] = event["event_id"]

    return updates


# ---------------------------------------------------------------------------
# apply_deterministic_rules
# ---------------------------------------------------------------------------


def apply_deterministic_rules(state: InterviewState) -> dict:
    event = state["incoming_event"]
    milestones = dict(state["milestones"])
    failed_run_count = state["failed_run_count"]
    candidate_status = state["candidate_status"]

    if event["type"] == "CODE_RUN_COMPLETED":
        if event["payload"].get("all_tests_passed"):
            milestones["IMPLEMENTS_CORRECT_SOLUTION"] = MilestoneRecord(
                status="COMPLETED",
                confidence=1.0,
                evidence_event_ids=[event["event_id"]],
            )
            failed_run_count = 0
        else:
            failed_run_count += 1

    hint_level = state["hint_level"]
    if event["type"] == "HINT_REQUESTED":
        hint_level += 1

    if (
        event["type"] == "CANDIDATE_IDLE"
        and event["payload"].get("duration_seconds", 0) >= 30
    ):
        candidate_status = "POSSIBLY_STUCK"

    if failed_run_count >= 3:
        candidate_status = "DEBUGGING_DIFFICULTY"

    return {
        "milestones": milestones,
        "failed_run_count": failed_run_count,
        "hint_level": hint_level,
        "candidate_status": candidate_status,
    }


# ---------------------------------------------------------------------------
# shared helpers
# ---------------------------------------------------------------------------

_EVENT_DESCRIPTIONS = {
    "CODE_SNAPSHOT": lambda p: f"[Candidate updated their code]\n{p.get('code', '')}",
    "CANDIDATE_IDLE": lambda p: (
        f"[Candidate has been idle for {p.get('duration_seconds', 0)}s]"
    ),
    "CODE_RUN_COMPLETED": lambda p: (
        f"[Candidate ran their code - all_tests_passed={p.get('all_tests_passed')}]"
    ),
    "HINT_REQUESTED": lambda p: "[Candidate explicitly requested a hint]",
}


def _event_context_message(event: InterviewEvent) -> Optional[HumanMessage]:
    """CANDIDATE_MESSAGE is already in state["messages"] via normalize_event -
    everything else needs a synthetic message so the LLM sees it happened."""
    render = _EVENT_DESCRIPTIONS.get(event["type"])
    if render is None:
        return None
    return HumanMessage(content=render(event["payload"]))


def _render_milestones_state(state: InterviewState) -> str:
    return "\n".join(
        f"- {milestone_id}: {record['status']} (confidence={record['confidence']})"
        for milestone_id, record in state["milestones"].items()
    )


# ---------------------------------------------------------------------------
# evaluate
# ---------------------------------------------------------------------------

EVALUATE_SYSTEM_PROMPT = """You are grading a candidate's progress in a Two Sum mock \
technical interview against a fixed rubric. You do not talk to the candidate directly \
- you only produce a structured evaluation of what just happened.

Rubric (milestone id: criteria):
{criteria}

Current milestone status:
{milestones_state}

Candidate status: {candidate_status}
Hint level so far: {hint_level}
Failed run count: {failed_run_count}

Only mark a milestone COMPLETED when the candidate has clearly satisfied its criteria \
based on actual evidence in the conversation - never assume something happened that \
wasn't said or shown. Only include milestones in your observations that have new \
evidence this turn."""


def evaluate(state: InterviewState) -> dict:
    model = get_chat_model().with_structured_output(EvaluationResult)

    system_prompt = EVALUATE_SYSTEM_PROMPT.format(
        criteria=render_milestone_criteria(),
        milestones_state=_render_milestones_state(state),
        candidate_status=state["candidate_status"],
        hint_level=state["hint_level"],
        failed_run_count=state["failed_run_count"],
    )

    turn_messages = list(state["messages"])
    context_message = _event_context_message(state["incoming_event"])
    if context_message is not None:
        turn_messages.append(context_message)

    messages = [SystemMessage(content=system_prompt), *turn_messages]
    result: EvaluationResult = model.invoke(messages)
    return {"pending_evaluation": result.model_dump()}


# ---------------------------------------------------------------------------
# update_milestones
# ---------------------------------------------------------------------------


_CANDIDATE_STATUS_SEVERITY = {
    "PROGRESSING": 0,
    "POSSIBLY_STUCK": 1,
    "DEBUGGING_DIFFICULTY": 2,
}


def update_milestones(state: InterviewState) -> dict:
    evaluation = state["pending_evaluation"]
    milestones = dict(state["milestones"])
    event_id = state["incoming_event"]["event_id"]

    for observation in evaluation["observations"]:
        milestone_id = observation["milestone_id"]
        if milestone_id not in milestones:
            continue  # defensively ignore a hallucinated milestone id
        evidence = milestones[milestone_id]["evidence_event_ids"]
        milestones[milestone_id] = MilestoneRecord(
            status=observation["status"],
            confidence=observation["confidence"],
            evidence_event_ids=[*evidence, event_id],
        )

    # apply_deterministic_rules already set state["candidate_status"] from hard
    # thresholds (failed_run_count, idle duration) earlier this turn - that's a
    # floor the LLM's own judgment call can escalate but never downgrade/override.
    candidate_status = max(
        state["candidate_status"],
        evaluation["candidate_status"],
        key=_CANDIDATE_STATUS_SEVERITY.__getitem__,
    )

    return {
        "milestones": milestones,
        "candidate_status": candidate_status,
        "recommended_action": evaluation["recommended_action"],
        "pending_evaluation": None,
    }


def route_action(state: InterviewState) -> str:
    if state["recommended_action"] in ("ask", "hint"):
        return "respond"
    return "finish_check"


# ---------------------------------------------------------------------------
# respond
# ---------------------------------------------------------------------------

RESPOND_TOOLS = [get_next_hint, retrieve_problem_context, search_general_programming_concept]
_RESPOND_TOOLS_BY_NAME = {tool.name: tool for tool in RESPOND_TOOLS}

RESPOND_SYSTEM_PROMPT = """You are swell, an AI coach running a mock Two Sum technical \
interview. Speak directly to the candidate in first person, as an interviewer would.

Coaching principles:
- Ask guiding questions before giving direct answers - help the candidate think, \
don't think for them.
- Never reveal the optimal solution or its approach (e.g. "hash map") unless the \
candidate has already proposed it themselves.
- If the recommended action is "hint", call get_next_hint with the candidate's \
current hint_level ({hint_level}) and phrase its result as a natural nudge - never \
just paste the raw hint text verbatim.
- If you need to check an edge case, the rubric, or a reference solution to answer \
accurately, call retrieve_problem_context.
- If the candidate asks a general programming/CS question unrelated to this specific \
problem, call search_general_programming_concept - never call it about Two Sum itself.
- Keep messages short - one or two sentences, like a real interviewer would say out \
loud.

Recommended action for this turn: {recommended_action}"""

_MAX_TOOL_ITERATIONS = 3


def respond(state: InterviewState) -> dict:
    model = get_chat_model().bind_tools(RESPOND_TOOLS)

    system_prompt = RESPOND_SYSTEM_PROMPT.format(
        hint_level=state["hint_level"],
        recommended_action=state["recommended_action"],
    )

    turn_messages = list(state["messages"])
    context_message = _event_context_message(state["incoming_event"])
    if context_message is not None:
        turn_messages.append(context_message)

    messages = [SystemMessage(content=system_prompt), *turn_messages]
    new_messages: list = []

    for _ in range(_MAX_TOOL_ITERATIONS):
        ai_message = model.invoke(messages)
        messages.append(ai_message)
        new_messages.append(ai_message)

        if not ai_message.tool_calls:
            break

        for call in ai_message.tool_calls:
            tool = _RESPOND_TOOLS_BY_NAME[call["name"]]
            result = tool.invoke(call["args"])
            tool_message = ToolMessage(content=str(result), tool_call_id=call["id"])
            messages.append(tool_message)
            new_messages.append(tool_message)

    return {"messages": new_messages}


# ---------------------------------------------------------------------------
# finish_check
# ---------------------------------------------------------------------------


def finish_check(state: InterviewState) -> dict:
    milestones = state["milestones"]
    done = (
        milestones["IMPLEMENTS_CORRECT_SOLUTION"]["status"] == "COMPLETED"
        and milestones["HANDLES_EDGE_CASES"]["status"] == "COMPLETED"
    )
    return {"status": "COMPLETED" if done else "IN_PROGRESS"}


def route_finish(state: InterviewState) -> str:
    return "generate_feedback" if state["status"] == "COMPLETED" else "__end__"


# ---------------------------------------------------------------------------
# generate_feedback
# ---------------------------------------------------------------------------

FEEDBACK_SYSTEM_PROMPT = """The mock interview is over. Write a short end-of-interview \
feedback report for the candidate, citing specific milestones and evidence from this \
session - never generic praise.

Final milestone status:
{milestones_state}"""


def generate_feedback(state: InterviewState) -> dict:
    model = get_chat_model()
    system_prompt = FEEDBACK_SYSTEM_PROMPT.format(
        milestones_state=_render_milestones_state(state)
    )
    messages = [SystemMessage(content=system_prompt), *state["messages"]]
    ai_message = model.invoke(messages)
    return {"messages": [ai_message]}
