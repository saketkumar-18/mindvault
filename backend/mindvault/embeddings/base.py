from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

import numpy as np


class EmbeddingProvider(Protocol):
    """Produces normalized float vectors for arbitrary text."""

    @property
    def name(self) -> str:
        ...

    @property
    def dim(self) -> int:
        ...

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        ...


def normalize(vectors: np.ndarray) -> np.ndarray:
    """L2-normalize rows in place-safe fashion."""
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return vectors / norms
