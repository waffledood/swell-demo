"""LLM-as-judge behavioral harness for the swell coaching graph, via LangSmith
Datasets/Evaluators (Task 5, deliverable 2/3).

RAGAS (run_ragas_eval.py) checks retrieval quality; this harness checks the
agent's actual turn-by-turn *behavior* against evals/dataset.yaml - things
RAGAS has no concept of, like "did the coach withhold the solution" or "was
the recommended_action appropriate given the state". Each dataset example is
a sequence of InterviewEvents; the target function replays them through a
fresh graph instance (one InMemorySaver + thread per example, same shape as
swell_agent/try_graph.py) and returns the final turn's state + transcript.
Evaluators mix deterministic checks (recommended_action/milestones/candidate_status
equality, banned-substring leak checks) with an LLM-as-judge evaluator that
grades free-text rubrics per example.

Run with: uv run python evals/run_langsmith_eval.py
"""

from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

import yaml
from dotenv import load_dotenv
from langgraph.checkpoint.memory import InMemorySaver
from langsmith import Client
from langsmith.evaluation import evaluate
from pydantic import BaseModel, Field

load_dotenv()

from swell_agent.graph import build_graph  # noqa: E402
from swell_agent.models import get_chat_model  # noqa: E402
from swell_agent.text import extract_text  # noqa: E402

DATASET_PATH = Path(__file__).parent / "dataset.yaml"
RESULTS_DIR = Path(__file__).parent / "results"
DATASET_NAME = "swell-two-sum-coach-eval"


# ---------------------------------------------------------------------------
# dataset load + upload
# ---------------------------------------------------------------------------


def load_entries() -> list[dict]:
    with DATASET_PATH.open() as f:
        return yaml.safe_load(f)


def ensure_dataset(client: Client, entries: list[dict]):
    if client.has_dataset(dataset_name=DATASET_NAME):
        client.delete_dataset(dataset_name=DATASET_NAME)

    dataset = client.create_dataset(
        DATASET_NAME,
        description=(
            "Golden behavioral eval set for the swell Two Sum coaching agent - "
            "expands the root README's Task 1 scenario table. See agent/evals/dataset.yaml."
        ),
    )
    client.create_examples(
        dataset_id=dataset.id,
        examples=[
            {
                "inputs": {"turns": entry["turns"]},
                "outputs": {"expected": entry.get("expected", {})},
                "metadata": {
                    "id": entry["id"],
                    "category": entry["category"],
                    "source": entry.get("source"),
                },
            }
            for entry in entries
        ],
    )
    return dataset


# ---------------------------------------------------------------------------
# target: replay a turn sequence through a fresh graph instance
# ---------------------------------------------------------------------------


def run_agent(inputs: dict) -> dict:
    turns = inputs["turns"]
    graph = build_graph(checkpointer=InMemorySaver())
    config = {"configurable": {"thread_id": f"eval-{uuid4()}"}}

    result = None
    transcript_lines: list[str] = []
    first_hint_response = None
    seen_hint_request = False
    prev_message_count = 0

    for i, turn in enumerate(turns):
        event = {**turn, "event_id": f"evt-{i}"}
        result = graph.invoke({"incoming_event": event}, config=config)

        messages = result["messages"]
        new_messages = messages[prev_message_count:]
        prev_message_count = len(messages)
        new_ai_texts = [
            extract_text(m) for m in new_messages if type(m).__name__ == "AIMessage"
        ]
        turn_text = " ".join(t for t in new_ai_texts if t)
        transcript_lines.append(
            f"[turn {i}: {turn['type']} recommended_action={result.get('recommended_action')}] "
            f"coach: {turn_text or '(no message this turn)'}"
        )

        if turn["type"] == "HINT_REQUESTED" and not seen_hint_request:
            seen_hint_request = True
            first_hint_response = turn_text

    last_message = result["messages"][-1] if result["messages"] else None
    final_message = (
        extract_text(last_message)
        if last_message is not None and type(last_message).__name__ == "AIMessage"
        else ""
    )

    return {
        "recommended_action": result.get("recommended_action"),
        "candidate_status": result.get("candidate_status"),
        "session_status": result.get("status"),
        "milestones": {mid: rec["status"] for mid, rec in result["milestones"].items()},
        "final_message": final_message,
        "first_hint_response": first_hint_response,
        "transcript": "\n".join(transcript_lines),
    }


# ---------------------------------------------------------------------------
# evaluators
# ---------------------------------------------------------------------------


def deterministic_state_match(outputs: dict, reference_outputs: dict) -> dict:
    expected = (reference_outputs or {}).get("expected", {})
    mismatches = []

    if "recommended_action" in expected:
        if outputs.get("recommended_action") != expected["recommended_action"]:
            mismatches.append(
                f"recommended_action: expected {expected['recommended_action']!r}, "
                f"got {outputs.get('recommended_action')!r}"
            )
    if "recommended_action_in" in expected:
        if outputs.get("recommended_action") not in expected["recommended_action_in"]:
            mismatches.append(
                f"recommended_action: expected one of {expected['recommended_action_in']}, "
                f"got {outputs.get('recommended_action')!r}"
            )
    if "candidate_status" in expected:
        if outputs.get("candidate_status") != expected["candidate_status"]:
            mismatches.append(
                f"candidate_status: expected {expected['candidate_status']!r}, "
                f"got {outputs.get('candidate_status')!r}"
            )
    if "session_status" in expected:
        if outputs.get("session_status") != expected["session_status"]:
            mismatches.append(
                f"session_status: expected {expected['session_status']!r}, "
                f"got {outputs.get('session_status')!r}"
            )
    if "milestones" in expected:
        actual = outputs.get("milestones", {})
        for milestone_id, status in expected["milestones"].items():
            if actual.get(milestone_id) != status:
                mismatches.append(
                    f"milestone {milestone_id}: expected {status!r}, got {actual.get(milestone_id)!r}"
                )

    has_checks = any(
        k in expected
        for k in ("recommended_action", "recommended_action_in", "candidate_status", "session_status", "milestones")
    )
    if not has_checks:
        return {"key": "deterministic_state_match", "score": None, "comment": "n/a - no deterministic checks configured"}

    return {
        "key": "deterministic_state_match",
        "score": 0 if mismatches else 1,
        "comment": "; ".join(mismatches) if mismatches else "all deterministic checks passed",
    }


def safety_no_leak(outputs: dict, reference_outputs: dict) -> dict:
    expected = (reference_outputs or {}).get("expected", {})
    banned = [s.lower() for s in expected.get("response_must_not_contain", [])]
    if not banned:
        return {"key": "safety_no_leak", "score": None, "comment": "n/a - no banned substrings configured"}

    text = (outputs.get("final_message") or "").lower()
    hits = [s for s in banned if s in text]
    return {
        "key": "safety_no_leak",
        "score": 0 if hits else 1,
        "comment": f"leaked banned substrings: {hits}" if hits else "no banned substrings found in final message",
    }


def hint_ladder_starts_correctly(outputs: dict, reference_outputs: dict) -> dict:
    expected = (reference_outputs or {}).get("expected", {})
    keywords = [k.lower() for k in expected.get("first_hint_keywords", [])]
    if not keywords:
        return {"key": "hint_ladder_level_one", "score": None, "comment": "n/a - no keywords configured"}

    text = (outputs.get("first_hint_response") or "").lower()
    missing = [k for k in keywords if k not in text]
    return {
        "key": "hint_ladder_level_one",
        "score": 0 if missing else 1,
        "comment": (
            f"first hint response missing expected level-1 keyword(s) {missing} - "
            f"got: {outputs.get('first_hint_response')!r}"
        )
        if missing
        else "first hint matched expected level-1 keyword(s)",
    }


class JudgeVerdict(BaseModel):
    passed: bool = Field(description="Whether the coach's behavior satisfies the rubric")
    reasoning: str = Field(description="One or two sentences explaining the verdict")


JUDGE_PROMPT = """You are grading an AI coding-interview coach's behavior against a rubric. \
Be strict - the rubric describes must-not-violate coaching principles (e.g. never leaking \
the solution, scaling hints appropriately, not ending the interview prematurely), not just \
"was the coach generally pleasant."

Rubric:
{rubric}

Full transcript of this session (one line per turn, showing the graph's recommended_action \
and the coach's message, if any):
{transcript}

Final coach message:
{final_message}

Does the coach's behavior across this transcript satisfy the rubric above?"""


def llm_judge_rubric(outputs: dict, reference_outputs: dict) -> dict:
    expected = (reference_outputs or {}).get("expected", {})
    rubric = expected.get("judge_rubric")
    if not rubric:
        return {"key": "llm_judge_rubric", "score": None, "comment": "n/a - no rubric configured"}

    judge = get_chat_model().with_structured_output(JudgeVerdict)
    verdict: JudgeVerdict = judge.invoke(
        JUDGE_PROMPT.format(
            rubric=rubric,
            transcript=outputs.get("transcript", ""),
            final_message=outputs.get("final_message", ""),
        )
    )
    return {
        "key": "llm_judge_rubric",
        "score": 1 if verdict.passed else 0,
        "comment": verdict.reasoning,
    }


EVALUATORS = [deterministic_state_match, safety_no_leak, hint_ladder_starts_correctly, llm_judge_rubric]


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------


def main() -> None:
    entries = load_entries()
    client = Client()
    ensure_dataset(client, entries)

    results = evaluate(
        run_agent,
        data=DATASET_NAME,
        evaluators=EVALUATORS,
        experiment_prefix="swell-baseline",
        max_concurrency=4,
    )

    # Iterate the raw result rows (not to_pandas(), which drops evaluator comments)
    # so the write-up's failure-mode analysis can cite the judge's actual reasoning,
    # not just a 0/1 score.
    records = []
    score_totals: dict[str, list[float]] = {}
    for row in results:
        run = row["run"]
        example = row["example"]
        eval_results = row["evaluation_results"]["results"]

        feedback = {}
        for r in eval_results:
            feedback[r.key] = {"score": r.score, "comment": r.comment}
            if r.score is not None:
                score_totals.setdefault(r.key, []).append(r.score)

        records.append(
            {
                "example_id": str(example.id),
                "metadata": example.metadata,
                "inputs": example.inputs,
                "reference_outputs": example.outputs,
                "outputs": run.outputs,
                "error": run.error,
                "feedback": feedback,
            }
        )

    means = {key: sum(scores) / len(scores) for key, scores in score_totals.items()}
    print("\n=== Mean scores (ignoring n/a) ===")
    for key, mean in means.items():
        print(f"{key}: {mean:.3f}  (n={len(score_totals[key])})")

    RESULTS_DIR.mkdir(exist_ok=True)
    with (RESULTS_DIR / "langsmith_results.json").open("w") as f:
        json.dump(records, f, indent=2, default=str, ensure_ascii=False)
    with (RESULTS_DIR / "langsmith_summary.json").open("w") as f:
        json.dump(
            {
                "experiment_name": getattr(results, "experiment_name", None),
                "mean_scores": means,
            },
            f,
            indent=2,
            default=str,
        )
    print(f"\nWrote results to {RESULTS_DIR}/")
    print(f"Experiment: {results.experiment_name}")


if __name__ == "__main__":
    main()
