"""Times the retriever separately from the one-time embed/build cost.

Run with: uv run python -m swell_agent.bench_retriever
"""

from __future__ import annotations

import time

from dotenv import load_dotenv

from swell_agent.retriever import _get_vectorstore, retrieve_problem_context

TEST_QUERIES = [
    "can the array have duplicate values?",
    "what's a good hint for two sum?",
    "what's the time complexity of the hash map approach?",
    "what happens with negative numbers?",
    "what counts as understanding the problem?",
]


def main() -> None:
    load_dotenv()

    start = time.perf_counter()
    _get_vectorstore()
    build_seconds = time.perf_counter() - start
    print(f"Build (load YAML + embed + index): {build_seconds:.3f}s\n")

    query_seconds: list[float] = []
    for query in TEST_QUERIES:
        start = time.perf_counter()
        result = retrieve_problem_context.invoke(query)
        elapsed = time.perf_counter() - start
        query_seconds.append(elapsed)
        print(f"{elapsed:.3f}s  {query}")
        print(f"{result}\n")

    print(
        f"\nQuery latency - avg: {sum(query_seconds) / len(query_seconds):.3f}s  "
        f"min: {min(query_seconds):.3f}s  max: {max(query_seconds):.3f}s"
    )


if __name__ == "__main__":
    main()
