from __future__ import annotations

import threading
from collections.abc import Sequence

import numpy as np

from mindvault.embeddings.base import normalize


class SentenceTransformerProvider:
    """Real semantic embeddings via sentence-transformers (local, offline).

    The model is downloaded once on first use and cached locally. Requires the
    optional ``mindvault[ml]`` extra.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2", *, dim: int = 384) -> None:
        self.model_name = model_name
        self.dim = dim
        self._model = None
        self._lock = threading.Lock()

    @property
    def name(self) -> str:
        return f"sentence-transformers:{self.model_name}"

    def _load(self):
        if self._model is None:
            with self._lock:
                if self._model is None:
                    from sentence_transformers import SentenceTransformer  # type: ignore[import-untyped]

                    self._model = SentenceTransformer(self.model_name)
        return self._model

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        model = self._load()
        vectors = model.encode(list(texts), convert_to_numpy=True, normalize_embeddings=True)
        vectors = np.asarray(vectors, dtype=np.float32)
        if vectors.ndim == 1:
            vectors = vectors.reshape(1, -1)
        return normalize(vectors).tolist()
