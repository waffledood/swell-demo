"""Import this BEFORE anything imports `ragas`.

ragas==0.2.15's ragas/llms/base.py unconditionally does
`from langchain_community.chat_models.vertexai import ChatVertexAI`, but that
submodule was removed from langchain-community in the 0.4.x line (its
integrations are being split into standalone packages - we don't use VertexAI
anywhere in this project, langchain-community just still has a hard import for
it). Pinning langchain-community back to a version that has it isn't viable
here: it would drag in an old langsmith pin that conflicts with the
langchain-core version the rest of the agent (langgraph, langchain-anthropic,
etc.) needs. Instead we stub the missing submodule in sys.modules before ragas
imports it - a small, contained workaround for a real ragas/langchain-community
version-skew bug, not a change to anything we actually use.
"""

from __future__ import annotations

import sys
import types

if "langchain_community.chat_models.vertexai" not in sys.modules:
    _stub = types.ModuleType("langchain_community.chat_models.vertexai")

    class ChatVertexAI:  # pragma: no cover - never instantiated, import-only shim
        def __init__(self, *args, **kwargs):
            raise RuntimeError(
                "ChatVertexAI is a compatibility stub (see _ragas_compat.py) - "
                "this project never uses VertexAI."
            )

    _stub.ChatVertexAI = ChatVertexAI
    sys.modules["langchain_community.chat_models.vertexai"] = _stub
