"""Tavily-backed web search tool, deliberately scoped to general
programming/CS concepts and never to the Two Sum problem itself.

An open-ended search tool could otherwise be used by the agent to look up
"Two Sum optimal solution" directly, leaking the answer the coach is meant to
withhold (see scenarios #1 and #4 in the root README.md's Task 1). The scope
guardrail here is enforced via the tool description, since that's what the
LLM reads to decide when to call it - retrieve_problem_context is the tool
for anything specific to Two Sum instead.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Annotated

from langchain_core.tools import tool
from langchain_tavily import TavilySearch


@lru_cache(maxsize=1)
def _get_search() -> TavilySearch:
    return TavilySearch(max_results=3)


@tool
def search_general_programming_concept(
    query: Annotated[
        str, "a general programming/CS concept question, decoupled from Two Sum"
    ],
) -> str:
    """Search the web for general programming/CS knowledge that is NOT specific to
    the Two Sum problem - e.g. language semantics ("is dict ordering guaranteed in
    Python 3.7+?"), general data structure concepts ("what's a hash collision?"), or
    complexity theory. Never use this to look up "Two Sum", "leetcode two sum", or
    anything shaped like this problem or its solution - use retrieve_problem_context
    for everything specific to Two Sum instead."""
    return _get_search().invoke(query)


if __name__ == "__main__":
    import sys

    from dotenv import load_dotenv

    load_dotenv()

    query = " ".join(sys.argv[1:]) or "is dict ordering guaranteed in Python 3.7+?"
    print(f"Query: {query}\n")
    print(search_general_programming_concept.invoke(query))
