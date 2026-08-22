from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Protocol


@dataclass(slots=True)
class LLMRequest:
    messages: list[dict[str, str]] = field(default_factory=list)
    system: str | None = None
    temperature: float = 0.2
    max_tokens: int = 1024
    stop: list[str] | None = None


@dataclass(slots=True)
class LLMResult:
    text: str
    model: str
    provider: str
    tokens_in: int = 0
    tokens_out: int = 0


class LLMProvider(Protocol):
    """Interface for local LLM backends.

    All providers must be fully local / offline. External API calls are never
    made by default.
    """

    name: str

    def available(self) -> bool:
        ...

    def generate(self, request: LLMRequest) -> Iterator[str]:
        ...

    def list_models(self) -> list[dict[str, object]]:
        ...


class InterruptedGeneration(Exception):
    """Raised inside ``generate()`` when the user requests cancellation."""