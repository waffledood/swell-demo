# Task 5 eval findings

Summary of what the eval harness in this directory found when run against the live deployed
agent. See `README.md`'s "## Task 5: Evals" section for the full methodology (dataset design,
harness architecture, judgment calls); this file is the condensed, action-oriented digest of
results and next steps.

## Harness built

`agent/evals/`: an 18-scenario behavioral dataset (`dataset.yaml`) + a 12-query retrieval dataset
(`retrieval_dataset.yaml`), a RAGAS harness (`run_ragas_eval.py`), and a LangSmith LLM-as-judge
harness (`run_langsmith_eval.py`) — all actually run against the real deployed agent, not just
scaffolded.

## Retrieval results (solid)

11/12 top-1 `doc_type` matches. Faithfulness **0.956**, context precision **0.917**, context
recall **0.917**.

## Behavioral results (more concerning)

- Deterministic state match: **64.7%** (11/17)
- LLM-judge rubric: **52.9%** (9/17)
- Safety (no-leak, deterministic check only): **100%** (5/5) — but see bug #3 below
- Hint-ladder-level-one: **0%** (0/1)

## Concrete bugs found, ranked by severity

1. **🔴 Crash bug**: `generate_feedback` throws `anthropic.BadRequestError` whenever the
   interview completes on a non-message event (e.g. code passing tests) — this is the *most
   natural* way an interview would actually end, meaning a real demo could crash mid-flow.
2. **Hint-ladder off-by-one**: the first hint always skips level 1 and jumps straight to level 2
   — an increment-then-lookup ordering bug between `apply_deterministic_rules` and
   `get_next_hint`.
3. **A real solution leak**: on the "candidate pastes the full solution" scenario, the coach said
   *"That looks like a solid one-pass hash map solution"* — confirming the answer rather than
   withholding it. The deterministic safety check missed this; only the LLM judge caught it. This
   is why `safety_no_leak`'s 100% score above is misleading on its own — it only measures banned
   substrings, not this kind of implicit confirmation.
4. **`recommended_action` selection is the noisiest dimension** — jumps to `hint` when `ask` is
   expected, and picks `wait` (no message at all) after tests pass when a follow-up was expected.
5. Milestone grading was mostly reliable, with one miss (`STATES_COMPLEXITY` skipped).

## Housekeeping note

The eval subagent's small `retriever.py` refactor (factoring out `retrieve_context_documents()`
for the RAGAS harness) landed inside an unrelated commit (`32ce823`, "move knowledge-base into
agent/") due to a race from two parallel sessions touching that file at the same time.
Functionally harmless, just means that commit's message doesn't fully describe its contents.

## Suggested next steps

Bug #1 (crash) should be fixed before any live demo, since it can trigger on the most natural
interview-ending path. Bugs #1-#4 are good candidates for Task 6's "identify and implement change
to at least one other piece of solution, demonstrate improvement with the eval harness" deliverable
— this harness already gives a before/after measurement path once fixes land.
