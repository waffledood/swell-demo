"""Deterministic milestone-criteria loader.

The evaluate node needs the full rubric every turn, not a top-k similarity
search - it's tiny (7 entries) and every criterion matters every time, so this
reads knowledge-base/two-sum/milestones.yaml directly rather than going
through the Qdrant retriever (which is for retrieve_problem_context's
open-ended lookups, not the evaluator's fixed rubric).
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml

DEFAULT_KNOWLEDGE_BASE_DIR = (
    Path(__file__).resolve().parents[1] / "knowledge-base" / "two-sum"
)


@lru_cache(maxsize=1)
def load_milestone_criteria() -> dict[str, str]:
    with (DEFAULT_KNOWLEDGE_BASE_DIR / "milestones.yaml").open() as f:
        data = yaml.safe_load(f)
    return {m["id"]: m["criteria"] for m in data["milestones"]}


def render_milestone_criteria() -> str:
    return "\n".join(
        f"- {milestone_id}: {criteria}"
        for milestone_id, criteria in load_milestone_criteria().items()
    )


if __name__ == "__main__":
    print(render_milestone_criteria())
