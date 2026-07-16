"""Loads the hand-authored Two Sum knowledge base into an in-memory Qdrant
collection and exposes it as a retriever tool for the LangGraph agent.

Rebuilt from knowledge-base/two-sum/*.yaml at process start (see README.md's
Task 3 "Chunking strategy" - one chunk per structural unit, matching the YAML
authoring boundaries rather than a generic text splitter).

Hints are deliberately NOT included here - see hints.py. A query like "what's
a good hint for two sum?" was found to rank the reference solution's code
above every actual hint, since the hint text never repeats the problem name
while the solution code literally contains the `two_sum` function name. Hints
are looked up deterministically by hint_level instead.
"""

from __future__ import annotations

import os
import time
from functools import lru_cache
from pathlib import Path
from typing import Annotated, Any, Literal, Optional

import cohere
import yaml
from langchain_core.documents import Document
from langchain_core.tools import tool
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import models

DEFAULT_EMBEDDING_MODEL = "text-embedding-3-small"
DEFAULT_RERANK_MODEL = "rerank-v3.5"
DEFAULT_KNOWLEDGE_BASE_DIR = (
    Path(__file__).resolve().parents[1] / "knowledge-base" / "two-sum"
)


def _load_yaml(path: Path) -> dict[str, Any]:
    with path.open() as f:
        return yaml.safe_load(f)


def _problem_documents(data: dict[str, Any], problem_id: str) -> list[Document]:
    documents = [
        Document(
            page_content=data["base_question"],
            metadata={"problem_id": problem_id, "doc_type": "base_question"},
        )
    ]

    for clarification in data.get("clarifications", []):
        documents.append(
            Document(
                page_content=(
                    f"Q: {clarification['question']}\nA: {clarification['answer']}"
                ),
                metadata={
                    "problem_id": problem_id,
                    "doc_type": "clarification",
                    "question": clarification["question"],
                },
            )
        )

    example_blocks = []
    for case in data.get("example_test_cases", []):
        block = f"Input: {case['input']}\nOutput: {case['output']}"
        if case.get("explanation"):
            block += f"\nExplanation: {case['explanation']}"
        example_blocks.append(block)
    if example_blocks:
        documents.append(
            Document(
                page_content="\n\n".join(example_blocks),
                metadata={"problem_id": problem_id, "doc_type": "example_test_cases"},
            )
        )

    constraints = data.get("constraints", [])
    if constraints:
        documents.append(
            Document(
                page_content="\n".join(f"- {c}" for c in constraints),
                metadata={"problem_id": problem_id, "doc_type": "constraints"},
            )
        )

    return documents


def _edge_case_documents(data: dict[str, Any], problem_id: str) -> list[Document]:
    return [
        Document(
            page_content=f"{case['name']}: {case['text']}",
            metadata={
                "problem_id": problem_id,
                "doc_type": "edge_case",
                "name": case["name"],
            },
        )
        for case in data.get("edge_cases", [])
    ]


def _reference_solution_documents(
    data: dict[str, Any], problem_id: str
) -> list[Document]:
    documents = []
    for solution in data.get("reference_solutions", []):
        complexity = solution.get("complexity", {})
        content = (
            f"Approach: {solution['approach']}\n"
            f"Time complexity: {complexity.get('time')}\n"
            f"Space complexity: {complexity.get('space')}\n\n"
            f"{solution['code']}"
        )
        documents.append(
            Document(
                page_content=content,
                metadata={
                    "problem_id": problem_id,
                    "doc_type": "reference_solution",
                    "approach": solution["approach"],
                    "time_complexity": complexity.get("time"),
                    "space_complexity": complexity.get("space"),
                },
            )
        )
    return documents


def _milestone_documents(data: dict[str, Any], problem_id: str) -> list[Document]:
    return [
        Document(
            page_content=f"{milestone['id']}: {milestone['criteria']}",
            metadata={
                "problem_id": problem_id,
                "doc_type": "milestone",
                "milestone_id": milestone["id"],
            },
        )
        for milestone in data.get("milestones", [])
    ]


def load_documents(
    knowledge_base_dir: Path = DEFAULT_KNOWLEDGE_BASE_DIR,
) -> list[Document]:
    """Load the hand-authored YAML knowledge base into one Document per structural unit."""
    problem = _load_yaml(knowledge_base_dir / "problem.yaml")
    problem_id = problem.get("problem_id", knowledge_base_dir.name)

    documents: list[Document] = []
    documents += _problem_documents(problem, problem_id)
    documents += _edge_case_documents(
        _load_yaml(knowledge_base_dir / "edge_cases.yaml"), problem_id
    )
    documents += _reference_solution_documents(
        _load_yaml(knowledge_base_dir / "reference_solutions.yaml"), problem_id
    )
    documents += _milestone_documents(
        _load_yaml(knowledge_base_dir / "milestones.yaml"), problem_id
    )
    return documents


@lru_cache(maxsize=1)
def _get_vectorstore() -> QdrantVectorStore:
    embeddings = OpenAIEmbeddings(
        model=os.environ.get("OPENAI_EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL),
        api_key=os.environ["OPENAI_API_KEY"],
    )
    return QdrantVectorStore.from_documents(
        documents=load_documents(),
        embedding=embeddings,
        location=":memory:",
        collection_name="two_sum_knowledge_base",
    )


DocType = Literal[
    "base_question",
    "clarification",
    "example_test_cases",
    "constraints",
    "edge_case",
    "reference_solution",
    "milestone",
]


@lru_cache(maxsize=1)
def _get_cohere_client() -> cohere.ClientV2:
    return cohere.ClientV2(api_key=os.environ["COHERE_API_KEY"])


_RERANK_MAX_RETRIES = 10
_RERANK_RETRY_DELAY_SECONDS = 7  # trial key: 10 calls/min ceiling -> ~6s/call pace


def _rerank(query: str, documents: list[Document], top_n: int) -> list[Document]:
    """Reorders documents by a dedicated cross-encoder reranker (Cohere
    rerank-v3.5) instead of trusting raw embedding-similarity order. Added for
    Task 6 - our one documented retrieval miss (edge-case-duplicates ranking
    the clarification chunk above the edge_case chunk) is exactly the kind of
    near-miss embedding similarity is bad at and rerankers are built for.

    Retries on 429s with a fixed delay matched to the actual rate limit -
    Cohere trial keys are capped at 10 calls/minute, so a real coaching
    session (or this eval suite's 12 back-to-back queries) can plausibly hit
    that ceiling; a short exponential backoff isn't generous enough for a
    hard per-minute cap."""
    if not documents:
        return documents

    for attempt in range(_RERANK_MAX_RETRIES):
        try:
            response = _get_cohere_client().rerank(
                model=DEFAULT_RERANK_MODEL,
                query=query,
                documents=[doc.page_content for doc in documents],
                top_n=top_n,
            )
            return [documents[result.index] for result in response.results]
        except cohere.errors.too_many_requests_error.TooManyRequestsError:
            if attempt == _RERANK_MAX_RETRIES - 1:
                raise
            time.sleep(_RERANK_RETRY_DELAY_SECONDS)

    return documents  # unreachable, satisfies type checkers


def retrieve_context_documents(
    query: str,
    doc_type: Optional[DocType] = None,
    k: int = 4,
    rerank: bool = True,
) -> list[Document]:
    """Shared retrieval path underneath retrieve_problem_context, returning raw
    Documents instead of the tool's joined string. Factored out so eval harnesses
    (see agent/evals/run_ragas_eval.py) can inspect individual retrieved chunks -
    e.g. per-chunk doc_type and page_content - without re-implementing the filter
    logic or re-parsing the tool's formatted output.

    rerank=False reproduces the pre-Task-6 baseline (plain top-k vector search)
    for before/after comparison; rerank=True (the default, used in production)
    over-fetches a wider candidate pool and reranks it down to k."""
    query_filter = None
    if doc_type is not None:
        query_filter = models.Filter(
            must=[
                models.FieldCondition(
                    key="metadata.doc_type", match=models.MatchValue(value=doc_type)
                )
            ]
        )

    if not rerank:
        return _get_vectorstore().similarity_search(query, k=k, filter=query_filter)

    candidate_pool_size = max(k * 2, 8)
    candidates = _get_vectorstore().similarity_search(
        query, k=candidate_pool_size, filter=query_filter
    )
    return _rerank(query, candidates, top_n=k)


@tool
def retrieve_problem_context(
    query: Annotated[str, "what to look up about the Two Sum problem"],
    doc_type: Annotated[
        Optional[DocType],
        (
            "restrict results to one category: base_question, clarification, "
            "example_test_cases, constraints, edge_case, reference_solution, or "
            "milestone. Omit to search across all of them. Never returns hints - "
            "use get_next_hint for those."
        ),
    ] = None,
) -> str:
    """Retrieve Two Sum coaching context: the problem statement, clarifications,
    edge cases, reference solutions, or milestone/rubric criteria. Use the doc_type
    filter whenever you know which category you need (e.g. milestone criteria) to
    avoid unrelated categories crowding out the right answer. Never use this for
    hints (use get_next_hint) or for general programming/CS questions unrelated to
    this problem (use web search for those instead)."""
    docs = retrieve_context_documents(query, doc_type=doc_type, k=4)
    if not docs:
        return "No matching context found in the knowledge base."

    return "\n\n---\n\n".join(
        f"[{doc.metadata.get('doc_type')}] {doc.page_content}" for doc in docs
    )


if __name__ == "__main__":
    import sys

    from dotenv import load_dotenv

    load_dotenv()

    query = " ".join(sys.argv[1:]) or "can the array have duplicate values?"
    print(f"Query: {query}\n")
    print(retrieve_problem_context.invoke({"query": query}))

