from __future__ import annotations

import re
from collections.abc import Sequence
from hashlib import md5

import numpy as np

from mindvault.embeddings.base import normalize

_TOKEN_RE = re.compile(r"[a-z0-9]+")


class HashEmbeddingProvider:
    """Deterministic, dependency-free local embedding provider.

    Uses feature-hashed word and bigram vectors. This is a **fallback**
    provider used when sentence-transformers is not installed: it gives
    reasonable lexical similarity but is not a true semantic model. When
    ``mindvault[ml]`` is installed, sentence-transformers is preferred.
    """

    name = "hash"
    dim: int

    def __init__(self, dim: int = 384) -> None:
        self.dim = dim

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        vectors: np.ndarray = np.zeros((len(texts), self.dim), dtype=np.float32)
        for row, text in enumerate(texts):
            tokens = _TOKEN_RE.findall((text or "").lower())
            if not tokens:
                continue
            for token in tokens:
                index = int.from_bytes(md5(token.encode()).digest()[:4], "little") % self.dim
                vectors[row, index] += 1.0
            for i in range(len(tokens) - 1):
                bigram = tokens[i] + " " + tokens[i + 1]
                index = int.from_bytes(md5(bigram.encode()).digest()[:4], "little") % self.dim
                vectors[row, index] += 0.7
        return normalize(vectors).tolist()
