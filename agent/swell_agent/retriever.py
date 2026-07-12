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
from functools import lru_cache
from pathlib import Path
from typing import Annotated, Any, Literal, Optional

import yaml
from langchain_core.documents import Document
from langchain_core.tools import tool
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import models

DEFAULT_EMBEDDING_MODEL = "text-embedding-3-small"
DEFAULT_KNOWLEDGE_BASE_DIR = (
    Path(__file__).resolve().parents[2] / "knowledge-base" / "two-sum"
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
    query_filter = None
    if doc_type is not None:
        query_filter = models.Filter(
            must=[
                models.FieldCondition(
                    key="metadata.doc_type", match=models.MatchValue(value=doc_type)
                )
            ]
        )

    docs = _get_vectorstore().similarity_search(query, k=4, filter=query_filter)
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

