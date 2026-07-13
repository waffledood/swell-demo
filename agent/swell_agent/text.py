"""Extracts candidate-facing text from a message's content.

Claude Sonnet 5 returns AIMessage.content as a list of content blocks (e.g.
{"type": "thinking", ...} alongside {"type": "text", ...}) rather than a plain
string whenever extended thinking is involved. Anything that displays a
message to the candidate - this test script today, the frontend chat UI later
- needs to extract only the text blocks, never show thinking blocks/signatures.
"""

from __future__ import annotations


def extract_text(message) -> str:
    content = message.content
    if isinstance(content, str):
        return content

    return "".join(
        block.get("text", "")
        for block in content
        if isinstance(block, dict) and block.get("type") == "text"
    )
