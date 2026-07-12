# CLAUDE.md

Context for Claude Code when working in this repo.

## What this repo is

This is the **single repo** for the **Certification Challenge** of an AI Engineering course (see
`Certification_Challenge.md` for the full assignment brief and `Cert Challenge Rubric.xlsx` for the
grading rubric). The rubric's "Status" column is the instructor's stock template (defaults to
mostly "Completed") — it does **not** reflect actual progress. Treat `README.md` as the source of
truth for what's actually done.

- **Due**: Thursday, July 16 2026, 7pm ET.
- **Submission format**: the brief asks for a single public GitHub repo containing a <=10 min Loom
  demo video (linked, not committed), a written document addressing every deliverable, and all
  relevant code. This repo now holds all three (video linked from `README.md`, the written
  document as `README.md` itself, and all application code) — previously this was split across
  this repo and a separate [`swell`](https://github.com/waffledood/swell) repo, but that split was
  consolidated here. `swell` is left as-is (unmaintained/historical); do not push new work there.

## The project: "swell"

An AI-powered software engineering coach that runs realistic mock technical (DSA) interviews —
chat + code editor + hints/feedback — so engineers can practice the *interactive* parts of an
interview (verbalizing reasoning, responding to hints, handling changing requirements), not just
solve problems in isolation like on LeetCode/HackerRank.

## Repo layout

- `README.md` — the written deliverable, one section per Certification Challenge task.
- `fe/` — the frontend app (Next.js, App Router). Renamed from `swell-fe` when consolidated in
  from the old `swell` repo; originally a ReactJS + Vite SPA, switched to Next.js so its
  `app/api/[...path]/route.js` Route Handler can act as the LLM gateway (hides `LANGGRAPH_API_URL`
  / `LANGSMITH_API_KEY` server-side — a pure SPA has no server runtime to hide them in). Needs
  `LANGGRAPH_API_URL` and `LANGSMITH_API_KEY` set (see `fe/.env.local.example`) to build or run.
- `knowledge-base/two-sum/` — hand-authored RAG source data for the midterm's single problem
  (`problem.yaml`, `hints.yaml`, `edge_cases.yaml`, `reference_solutions.yaml`,
  `milestones.yaml`). See Task 3 in `README.md` for the chunking strategy these files are meant to
  support (one chunk per structural unit/entry).
- `media/` — diagrams (e.g. `swell-arch.svg`) referenced from `README.md`.
- No backend/agent code exists yet — that's Task 4, still to be built.

## Task-to-deliverable map

The Certification Challenge is organized into 7 tasks; `README.md` is the running written
document that answers all of them in order. Current state:

| Task | Topic | Status in README |
|---|---|---|
| 1 | Problem, audience, scope (workflow diagram, eval questions) | Done |
| 2 | Proposed solution (infra diagram, agent workflow diagram, state model) | Done |
| 3 | Data strategy (chunking, external API/data sources) | Done |
| 4 | End-to-end prototype + deployment | In progress — `fe/` (Next.js, with LLM gateway route), and `knowledge-base/` are in place; agent/backend and deployment still needed |
| 5 | Evals (test set + harness + conclusions) | Not started |
| 6 | Advanced retrieval + one more improvement, with before/after comparison | Not started |
| 7 | Next steps / Demo Day reflection | Not started |

When picking up work, check which task is next in this table rather than assuming the rubric
spreadsheet's status column.

## Stack decisions made so far

Decided (visible in `media/swell-arch.svg` and `README.md`'s infrastructure diagram):

- **Frontend**: Next.js, App Router (`fe/`)
- **LLM gateway**: Next.js Route Handler (`fe/app/api/[...path]/route.js`, via
  `langgraph-nextjs-api-passthrough`) — client calls same-origin `/api/*` only; the Route Handler
  forwards server-side to the LangGraph deployment. Satisfies the brief's "use an LLM gateway"
  requirement. Note: the passthrough package itself warns this pattern is no longer LangGraph's
  recommended auth approach — implementing custom auth directly in the LangGraph deployment
  (Python/TS `custom_auth`) is the current recommendation and worth revisiting once Task 4's agent
  backend exists.
- **LLM**: `claude-sonnet-5`
- **Agent orchestration**: LangGraph
- **Tools**: retriever over Qdrant (problem-specific RAG), Tavily search (scoped to general
  programming/CS concepts, never the problem/solution itself — see Task 3 in `README.md`)
- **Embedding model**: OpenAI `text-embedding-3-small`
- **Vector DB**: Qdrant
- **Monitoring**: LangSmith, LangGraph Studio
- **Evaluation framework**: RAGAS (retrieval-quality metrics) + LLM-as-judge via LangSmith
  Datasets/Evaluators (behavioral/rubric grading) — see Task 3 discussion for why RAGAS alone
  isn't sufficient here
- **State/session persistence**: PostgreSQL
- **Deployment**: Vercel (Next.js app: frontend + LLM gateway), LangGraph Platform (agent)
- Architecture also includes a load balancer layer (auth, rate-limiting) and an event
  collector/processor in front of the agent orchestrator (see the `CANDIDATE_MESSAGE` /
  `CODE_SNAPSHOT` / `CANDIDATE_IDLE` event types documented in the README). The Next.js gateway is
  deliberately a thin passthrough (auth/rate-limiting/forwarding only) — event normalization and
  deterministic rules stay in the Python LangGraph agent, not the gateway, to avoid duplicating
  that logic across two languages.

**Still open / not yet decided** — do not assume or invent a specific choice here; surface it as
an open decision when it becomes relevant:

- Backend web framework/language for the agent/session-persistence layer itself (the LLM gateway
  question is now resolved by Next.js above, but the LangGraph agent + Postgres persistence layer
  behind it still needs a framework/language)

## Working conventions

- Application code now lives in this repo (`fe/`, `knowledge-base/`, and future backend/agent
  code) alongside the written document — don't assume it belongs elsewhere.
- Diagrams in the README use Mermaid (inline) for flowcharts; the infra diagram is a standalone
  SVG in `media/`.
- Keep `README.md` structured as one section per Certification Challenge task, matching the
  numbering in `Certification_Challenge.md`, so it can be graded/read against the rubric directly.
- When writing up Tasks 4-7 in `README.md`, cross-reference the relevant code/commits in this
  repo where useful (e.g. linking to the chunking implementation, the eval harness, etc.).
