from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol


@dataclass(slots=True)
class VectorHit:
    id: str
    score: float


class VectorStore(Protocol):
    """Stores vectors keyed by string IDs and answers k-NN queries.

    Implementations are swappable: FAISS (production, when installed) or a
    pure-NumPy index (fallback, always available).
    """

    dim: int
    backend: str

    def add(self, ids: Sequence[str], vectors: Sequence[Sequence[float]]) -> None:
        ...

    def remove(self, ids: Sequence[str]) -> None:
        ...

    def query(self, vector: Sequence[float], top_k: int) -> list[VectorHit]:
        ...

    def count(self) -> int:
        ...

    def save(self) -> None:
        ...

    def load(self) -> None:
        ...

    def ids(self) -> list[str]:
        ...
