from __future__ import annotations

import re
from collections.abc import Iterator

from mindvault.llm.base import LLMRequest


class MockLLMProvider:
    """Deterministic test provider that echoes the context.

    Used only in test suites and development environments where a real model
    is unavailable. Never enabled in production.
    """

    name = "mock"

    def available(self) -> bool:
        return True

    def list_models(self) -> list[dict[str, object]]:
        return [{"name": "mock-model", "provider": "mock", "size": 0, "status": "available"}]

    def generate(self, request: LLMRequest) -> Iterator[str]:
        """Produce a deterministic response that references the provided context.

        The output always includes a ``[1]`` citation so that tests can verify
        the citation pipeline end-to-end.
        """
        user_text = " ".join(
            m["content"] for m in request.messages if m["role"] == "user"
        )
        # Extract the first numbered source's text from the prompt
        doc_match = re.search(r"\[1\][^\n]*\n(.*?)(?:\n\[2\]|\n</documents>|\Z)", user_text, re.DOTALL)
        if doc_match:
            excerpt = doc_match.group(1).strip()[:200]
            yield f"Based on the provided documents:\n\n{excerpt}\n\n[1]"
        else:
            yield "I couldn't find enough information in your documents."