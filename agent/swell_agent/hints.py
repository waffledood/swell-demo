"""Deterministic hint-ladder lookup.

No embedding/similarity search needed here: the agent's session state already
tracks hint_level directly (see the root README.md's core state model), so
"what's the next hint" is a plain lookup by level, not a retrieval problem.
This also sidesteps a real failure mode we found in retrieve_problem_context -
a generic "hint" query scored the reference solution's code higher than the
actual hints, since the hint text never repeats the problem name. Hints are
deliberately excluded from the Qdrant collection entirely; this is the only
path to them.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Annotated

import yaml
from langchain_core.tools import tool

DEFAULT_KNOWLEDGE_BASE_DIR = (
    Path(__file__).resolve().parents[1] / "knowledge-base" / "two-sum"
)


@lru_cache(maxsize=1)
def _load_hints() -> list[dict]:
    with (DEFAULT_KNOWLEDGE_BASE_DIR / "hints.yaml").open() as f:
        data = yaml.safe_load(f)
    return sorted(data["hints"], key=lambda hint: hint["level"])


@tool
def get_next_hint(
    hint_level: Annotated[int, "the candidate's current hint_level from session state"],
) -> str:
    """Look up the hint at the candidate's current hint_level. apply_deterministic_rules
    increments hint_level (in nodes.py) before this is called, so by the time this runs,
    hint_level already IS the level to show - e.g. the first-ever HINT_REQUESTED bumps
    hint_level from 0 to 1, and this looks up level 1 directly (previously looked up
    hint_level + 1 = 2, silently skipping level 1 on every session's first hint).
    Deterministic lookup by level: never returns the reference solution, and never
    skips ahead. Use this instead of retrieve_problem_context whenever the candidate
    needs a hint."""
    for hint in _load_hints():
        if hint["level"] == hint_level:
            return hint["text"]
    return "No further hints available - this is the most specific hint in the ladder."


if __name__ == "__main__":
    import sys

    hint_level = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    print(f"hint_level: {hint_level}\n")
    print(get_next_hint.invoke({"hint_level": hint_level}))
