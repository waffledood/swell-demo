"""Shared chat model factory for the swell agent."""

from __future__ import annotations

import os

from langchain_anthropic import ChatAnthropic

DEFAULT_MODEL = "claude-sonnet-5"


def get_chat_model(**kwargs) -> ChatAnthropic:
    kwargs.setdefault("thinking", {"type": "disabled"})
    return ChatAnthropic(
        model=os.environ.get("ANTHROPIC_MODEL", DEFAULT_MODEL),
        api_key=os.environ.get("ANTHROPIC_API_KEY"),
        **kwargs,
    )
