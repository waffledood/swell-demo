# swell frontend

Next.js (App Router) app: the chat + code-editor workspace UI, plus an `/api/*` Route Handler that acts as the LLM gateway in front of the LangGraph agent.

## Setup

```sh
npm install
cp .env.local.example .env.local
# fill in LANGGRAPH_API_URL and LANGSMITH_API_KEY in .env.local
npm run dev
```

`LANGGRAPH_API_URL` and `LANGSMITH_API_KEY` are required to build or run this app — they're read server-side only (in `app/api/[...path]/route.js`) and are never sent to the browser. See the "LLM gateway" entry in the root `README.md`'s Task 2 for why this exists.

## Verify

```sh
npm run lint
npm run build
```
