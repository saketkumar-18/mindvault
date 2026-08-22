from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import numpy as np

from mindvault.embeddings.base import normalize
from mindvault.errors import IndexUnavailable
from mindvault.vectorstore.base import VectorHit


class NumpyVectorStore:
    """Dependency-free cosine-similarity vector index persisted to disk.

    Loads vectors into memory on demand. Suitable for local-first use; FAISS is
    preferred when installed. Matrices are saved as NumPy ``.npz`` files.
    """

    backend = "numpy"

    def __init__(self, path: Path, dim: int) -> None:
        self.path = path
        self.dim = dim
        self._ids: list[str] = []
        self._vectors: np.ndarray = np.zeros((0, dim), dtype=np.float32)

    # -- persistence -----------------------------------------------------
    def save(self) -> None:
        if len(self._ids) == 0:
            if self.path.exists():
                self.path.unlink()
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(
            self.path,
            vectors=self._vectors,
            ids=np.array(self._ids, dtype="<U256"),
        )

    def load(self) -> None:
        if not self.path.exists():
            self._ids = []
            self._vectors = np.zeros((0, self.dim), dtype=np.float32)
            return
        try:
            data = np.load(self.path, allow_pickle=False)
            vectors = np.asarray(data["vectors"], dtype=np.float32)
            ids = [str(x) for x in data["ids"]]
        except Exception as exc:
            raise IndexUnavailable(
                "Vector index is missing or corrupt.",
                suggestion="Open Settings > Indexes and rebuild the index.",
            ) from exc
        if vectors.shape[1] != self.dim:
            raise IndexUnavailable(
                f"Vector index dimension mismatch (index={vectors.shape[1]}, expected={self.dim}).",
                suggestion="Rebuild the index after changing the embedding model.",
            )
        self._vectors = vectors
        self._ids = ids

    # -- mutation --------------------------------------------------------
    def add(self, ids: Sequence[str], vectors: Sequence[Sequence[float]]) -> None:
        if not ids:
            return
        new_vecs = normalize(np.asarray(vectors, dtype=np.float32).reshape(len(ids), self.dim))
        existing = {id_: i for i, id_ in enumerate(self._ids)}
        keep_mask: np.ndarray = np.ones(len(self._ids), dtype=bool)
        for id_ in ids:
            if id_ in existing:
                keep_mask[existing[id_]] = False
        self._ids = [self._ids[i] for i in range(len(self._ids)) if keep_mask[i]]
        self._vectors = self._vectors[keep_mask]
        self._ids.extend(ids)
        self._vectors = np.vstack([self._vectors, new_vecs]) if self._vectors.size else new_vecs

    def remove(self, ids: Sequence[str]) -> None:
        if not ids:
            return
        drop = {id_ for id_ in ids}
        keep = [i for i, id_ in enumerate(self._ids) if id_ not in drop]
        self._ids = [self._ids[i] for i in keep]
        self._vectors = self._vectors[keep] if keep else np.zeros((0, self.dim), dtype=np.float32)

    # -- query -----------------------------------------------------------
    def query(self, vector: Sequence[float], top_k: int) -> list[VectorHit]:
        if len(self._ids) == 0:
            return []
        query_vec = normalize(np.asarray(vector, dtype=np.float32).reshape(1, self.dim))
        scores = self._vectors @ query_vec.T
        scores = scores.flatten()
        top = min(top_k, len(scores))
        if top == 0:
            return []
        indices = np.argpartition(-scores, top - 1)[:top]
        indices = indices[np.argsort(-scores[indices])]
        return [VectorHit(id=self._ids[i], score=float(scores[i])) for i in indices]

    def count(self) -> int:
        return len(self._ids)

    def ids(self) -> list[str]:
        return list(self._ids)
