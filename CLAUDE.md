# CLAUDE.md

Context for Claude Code when working in this repo.

## What this repo is

This is a **course submission / written-deliverables repo**, not where the application code lives.
It's being built for the **Certification Challenge** of an AI Engineering course (see
`Certification_Challenge.md` for the full assignment brief and `Cert Challenge Rubric.xlsx` for the
grading rubric). The rubric's "Status" column is the instructor's stock template (defaults to
mostly "Completed") — it does **not** reflect actual progress. Treat `README.md` as the source of
truth for what's actually done.

- **Due**: Thursday, July 16 2026, 7pm ET.
- **Submission format**: the brief asks for a single public GitHub repo containing a <=10 min Loom
  demo video (linked, not committed), a written document addressing every deliverable, and all
  relevant code. The user has split this across **two repos**:
  - `swell-demo` (this repo): written document (`README.md`), diagrams, planning artifacts.
  - [`swell`](https://github.com/waffledood/swell): the actual application code (frontend,
    backend, agent, evals, etc.).
  - Since the brief technically expects one repo with everything, make sure the final `README.md`
    clearly links to the `swell` repo (and vice versa) so a grader can navigate between them.

## The project: "swell"

An AI-powered software engineering coach that runs realistic mock technical (DSA) interviews —
chat + code editor + hints/feedback — so engineers can practice the *interactive* parts of an
interview (verbalizing reasoning, responding to hints, handling changing requirements), not just
solve problems in isolation like on LeetCode/HackerRank.

## Task-to-deliverable map

The Certification Challenge is organized into 7 tasks; `README.md` is the running written
document that answers all of them in order. Current state:

| Task | Topic | Status in README |
|---|---|---|
| 1 | Problem, audience, scope (workflow diagram, eval questions) | Done |
| 2 | Proposed solution (infra diagram, agent workflow diagram, state model) | Done |
| 3 | Data strategy (chunking, external API/data sources) | Not started |
| 4 | End-to-end prototype + deployment | Not started (code lives in the separate `swell` repo, not here) |
| 5 | Evals (test set + harness + conclusions) | Not started |
| 6 | Advanced retrieval + one more improvement, with before/after comparison | Not started |
| 7 | Next steps / Demo Day reflection | Not started |

When picking up work, check which task is next in this table rather than assuming the rubric
spreadsheet's status column.

## Stack decisions made so far

Decided (visible in `media/swell-arch.svg` and `README.md`'s infrastructure diagram):

- **Frontend**: ReactJS + Vite
- **Agent orchestration**: LangGraph
- **Monitoring**: LangSmith
- **Vector DB**: Qdrant
- **State/session persistence**: PostgreSQL
- **Deployment**: Vercel
- Architecture also includes a load balancer layer (auth, rate-limiting) and an event
  collector/processor in front of the agent orchestrator (see the `CANDIDATE_MESSAGE` /
  `CODE_SNAPSHOT` / `CANDIDATE_IDLE` event types documented in the README).

**Still open / not yet decided** — do not assume or invent a specific choice here; surface it as
an open decision when it becomes relevant (Task 2 deliverable 2 and Task 3 onward require these to
be named explicitly):

- LLM provider/model(s)
- Embedding model
- External/agentic search API (the brief suggests Tavily as an example, not a requirement)
- Evaluation framework (the brief suggests RAGAS and LLM-as-judge as examples, not a requirement)
- Backend web framework/language

## Working conventions

- This repo intentionally has no application code — that lives in the separate
  [`swell`](https://github.com/waffledood/swell) repo. Don't scaffold a backend/frontend structure
  here; if asked to build the prototype, confirm whether the work should happen in this repo or
  in `swell` before writing code.
- Diagrams in the README use Mermaid (inline) for flowcharts; the infra diagram is a standalone
  SVG in `media/`.
- Keep `README.md` structured as one section per Certification Challenge task, matching the
  numbering in `Certification_Challenge.md`, so it can be graded/read against the rubric directly.
- When writing up Tasks 3-7 in `README.md`, cross-reference the relevant code/commits in the
  `swell` repo where useful (e.g. linking to the chunking implementation, the eval harness, etc.).
