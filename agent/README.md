# swell agent

Python/LangGraph coaching agent, deployed to LangGraph Platform. Uses `uv` for dependency management.

## Setup

```sh
uv sync
cp .env.example .env
# fill in OPENAI_API_KEY in .env
```

## Retriever

`swell_agent/retriever.py` loads `knowledge-base/two-sum/*.yaml` into an in-memory Qdrant collection (rebuilt at process start - see the root `README.md`'s Task 3 for why) and exposes it as `retrieve_problem_context`, a `@tool`-decorated retriever for the LangGraph agent to call.

Try it manually:

```sh
uv run python -m swell_agent.retriever "can the array have duplicate values?"
```
