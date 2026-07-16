# Deliverables Traceability

Maps every deliverable in the grading rubric (`Cert Challenge Rubric.xlsx`) to where it's answered
in `README.md` and, where applicable, the exact code that implements it. Deliverable text is
quoted verbatim from the rubric.

## Task 1: Defining Problem, Audience, and Scope

| # | Deliverable (rubric text) | Points | README | Code |
| --- | --- | --- | --- | --- |
| 1.1 | "Write a succinct 1-sentence description of the problem" | 1 | [Task 1](README.md#task-1-defining-problem-audience-and-scope), opening sentence | — |
| 1.2 | "Write 1-2 paragraphs on why this is a problem for your specific user" | 3 | [Task 1](README.md#task-1-defining-problem-audience-and-scope), paragraphs 2-3 | — |
| 1.3 | "Create a workflow diagram illustrating how the user solves this problem today." | 3 | [Task 1](README.md#task-1-defining-problem-audience-and-scope), Mermaid flowchart | — |
| 1.4 | "Create a list of questions or input-output pairs that you can use to evaluate your application" | 2 | [Task 1](README.md#task-1-defining-problem-audience-and-scope), scenario table (11 rows) | Expanded into a real eval dataset: [`agent/evals/dataset.yaml`](agent/evals/dataset.yaml) |

## Task 2: Propose a Solution

| # | Deliverable (rubric text) | Points | README | Code |
| --- | --- | --- | --- | --- |
| 2.1 | "Describe your solution in one sentence." | 1 | [Task 2](README.md#task-2-propose-a-solution), opening sentence | — |
| 2.2 | "Create an infrastructure diagram of your stack... Write one sentence on why you made each tooling choice." | 7 | [Infrastructure Diagram](README.md#infrastructure-diagram) | [`media/swell-arch.svg`](media/swell-arch.svg) (diagram); every listed technology is actually implemented, see Task 3-6 rows below for specifics |
| 2.3 | "Create an Agent Workflow Diagram illustrating how your application solves the user's problem from end to end." | 7 | [Agent Workflow Diagram](README.md#agent-workflow-diagram), [Core state model](README.md#core-state-model), [Event processing flow](README.md#event-processing-flow), [Deterministic Rules](README.md#deterministic-rules) | The diagram is implemented as a real LangGraph: [`agent/swell_agent/graph.py`](agent/swell_agent/graph.py) (wiring), [`agent/swell_agent/nodes.py`](agent/swell_agent/nodes.py) (all 6 nodes), [`agent/swell_agent/state.py`](agent/swell_agent/state.py) (state schema) |

## Task 3: Dealing with the Data

| # | Deliverable (rubric text) | Points | README | Code |
| --- | --- | --- | --- | --- |
| 3.1 | "Describe all of your data sources and external APIs, and describe what you'll use them for." | 5 | [Data sources and external API](README.md#data-sources-and-external-api) | Data sources: [`agent/knowledge-base/two-sum/`](agent/knowledge-base/two-sum/) (5 YAML files). Retriever tool: [`agent/swell_agent/retriever.py:268-283`](agent/swell_agent/retriever.py#L268-L283) (`retrieve_problem_context`). External API (Tavily): [`agent/swell_agent/web_search.py:27`](agent/swell_agent/web_search.py#L27) (`search_general_programming_concept`), scoped per the README's leak-prevention reasoning |
| 3.2 | "Describe the default chunking strategy that you will use. Why did you make this decision?" | 5 | [Chunking strategy](README.md#chunking-strategy) | One-chunk-per-structural-unit implemented in [`agent/swell_agent/retriever.py:43-140`](agent/swell_agent/retriever.py#L43-L140) (`_problem_documents`, `_edge_case_documents`, `_reference_solution_documents`, `_milestone_documents`) |

## Task 4: Build End-to-End Prototype

| # | Deliverable (rubric text) | Points | README | Code |
| --- | --- | --- | --- | --- |
| 4.1 | "Build an end-to-end prototype and deploy to with a front end using a tool like Vercel" | 15 | No dedicated README section (CLAUDE.md's task table links here) — evidenced directly by the live deployment and the code | **Frontend** (deployed to Vercel, `tryswell.vercel.app`): [`fe/components/workspace.jsx`](fe/components/workspace.jsx) (Problem/Editor layout), [`fe/components/chat.jsx`](fe/components/chat.jsx) (chat panel, `useStream`), [`fe/app/api/[...path]/route.js`](fe/app/api/%5B...path%5D/route.js) (LLM gateway). **Agent** (deployed to LangGraph Platform): [`agent/swell_agent/graph.py`](agent/swell_agent/graph.py), [`agent/langgraph.json`](agent/langgraph.json) (deployment config). **Local verification**: [`agent/swell_agent/try_graph.py`](agent/swell_agent/try_graph.py) |

## Task 5: Evals

| # | Deliverable (rubric text) | Points | README | Code |
| --- | --- | --- | --- | --- |
| 5.1 | "Prepare a test data set (either by generating synthetic data or by assembling an existing dataset)" | 2 | [Test dataset](README.md#test-dataset) | [`agent/evals/dataset.yaml`](agent/evals/dataset.yaml) (18 behavioral scenarios), [`agent/evals/retrieval_dataset.yaml`](agent/evals/retrieval_dataset.yaml) (12 retrieval queries) |
| 5.2 | "Create an evaluation harness that's relevant to your problem space" | 10 | [Evaluation harness](README.md#evaluation-harness) | [`agent/evals/run_ragas_eval.py`](agent/evals/run_ragas_eval.py) (RAGAS), [`agent/evals/run_langsmith_eval.py`](agent/evals/run_langsmith_eval.py) (LangSmith LLM-as-judge), [`agent/evals/_ragas_compat.py`](agent/evals/_ragas_compat.py) (compat shim) |
| 5.3 | "What conclusions can you draw about the performance and effectiveness of your pipeline with this information?" | 3 | [Results and conclusions](README.md#results-and-conclusions) | Raw results: [`agent/evals/results/`](agent/evals/results/); condensed findings: [`agent/evals/FINDINGS.md`](agent/evals/FINDINGS.md); filed as GitHub issues [#1](https://github.com/waffledood/swell-demo/issues/1) [#2](https://github.com/waffledood/swell-demo/issues/2) [#3](https://github.com/waffledood/swell-demo/issues/3) [#4](https://github.com/waffledood/swell-demo/issues/4) |

## Task 6: Improving Your Prototype

| # | Deliverable (rubric text) | Points | README | Code |
| --- | --- | --- | --- | --- |
| 6.1 | "Choose and implement an advanced retrieval technique... Write 1-2 sentences on why you believe it will be useful for your use case." | 6 | [Advanced retrieval: reranking](README.md#advanced-retrieval-reranking-cohere-rerank-v35) | [`agent/swell_agent/retriever.py:201-231`](agent/swell_agent/retriever.py#L201-L231) (`_rerank`), wired into [`retrieve_context_documents`](agent/swell_agent/retriever.py#L233) via the `rerank` param |
| 6.2 | "How does the performance compare to your original RAG application? Provide results in a table." | 2 | [Advanced retrieval: reranking](README.md#advanced-retrieval-reranking-cohere-rerank-v35), results table | Before: [`agent/evals/results/ragas_summary_baseline.json`](agent/evals/results/ragas_summary_baseline.json). After: [`agent/evals/results/ragas_summary.json`](agent/evals/results/ragas_summary.json). Reproducible via `uv run python evals/run_ragas_eval.py [--no-rerank]` |
| 6.3 | "Identify and implement change to at least one other piece of solution. Using the evaluation harness as hard evidence, demonstrate a meaningfully improved response" | 6 | [One other improvement: hint-ladder off-by-one fix](README.md#one-other-improvement-hint-ladder-off-by-one-fix) | Fix: [`agent/swell_agent/hints.py:34-45`](agent/swell_agent/hints.py#L34-L45) (`get_next_hint`). Before: [`agent/evals/results/langsmith_summary_baseline.json`](agent/evals/results/langsmith_summary_baseline.json). After: [`agent/evals/results/langsmith_summary.json`](agent/evals/results/langsmith_summary.json) |

## Task 7: Next Steps

| # | Deliverable (rubric text) | Points | README | Code |
| --- | --- | --- | --- | --- |
| 7.1 | "Reflecting on what you've built so far, what parts of your current implementation do you plan to keep for Demo Day, and what parts would you change or improve?" | 2 | [What we're keeping for Demo Day](README.md#what-were-keeping-for-demo-day), [What we'd change or improve](README.md#what-wed-change-or-improve) | — |

## Final Submission

| # | Deliverable (rubric text) | Points | Location |
| --- | --- | --- | --- |
| F.1 | "A 10-minute (OR LESS) loom video of a live demo of your application that also describes the use case." | 10 | https://youtu.be/3bcF3ELRArY (linked at the top of [`README.md`](README.md); hosted on YouTube rather than Loom, same requirement) |
| F.2 | "A written document addressing each deliverable and answering each question" | 10 | [`README.md`](README.md) (this traceability doc cross-references it deliverable-by-deliverable) |
| F.3 | "All relevant code" | 0 | This repo: [`fe/`](fe/) (frontend), [`agent/`](agent/) (LangGraph agent + evals + knowledge base) |
