from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path

import numpy as np

from mindvault.embeddings.base import normalize
from mindvault.errors import IndexUnavailable
from mindvault.vectorstore.base import VectorHit


class FaissVectorStore:
    """FAISS-backed inner-product index over L2-normalized vectors.

    Requires the optional ``mindvault[ml]`` extra (``faiss-cpu``).
    A mirror matrix is kept in memory so removals/rebuilds stay exact.
    """

    backend = "faiss"

    def __init__(self, path: Path, dim: int) -> None:
        try:
            import faiss  # type: ignore[import-untyped]
        except ImportError as exc:  # pragma: no cover
            raise IndexUnavailable(
                "FAISS is not installed.",
                suggestion="Install the ML extra: pip install mindvault[ml]",
            ) from exc
        self.faiss = faiss
        self.path = path
        self.dim = dim
        self._ids: list[str] = []
        self._matrix: np.ndarray = np.zeros((0, dim), dtype=np.float32)
        self._index = faiss.IndexFlatIP(dim)

    def _rebuild_index(self) -> None:
        self._index = self.faiss.IndexFlatIP(self.dim)
        if len(self._matrix) > 0:
            self._index.add(self._matrix)

    # -- persistence -----------------------------------------------------
    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.faiss.write_index(self._index, str(self.path))
        ids_path = self.path.with_suffix(".ids.json")
        ids_path.write_text(json.dumps(self._ids), encoding="utf-8")

    def load(self) -> None:
        index_path = self.path
        ids_path = self.path.with_suffix(".ids.json")
        if not index_path.exists() or not ids_path.exists():
            self._index = self.faiss.IndexFlatIP(self.dim)
            self._matrix = np.zeros((0, self.dim), dtype=np.float32)
            self._ids = []
            return
        try:
            self._index = self.faiss.read_index(str(index_path))
            self._ids = json.loads(ids_path.read_text(encoding="utf-8"))
            self._matrix = self._index.reconstruct_n(0, self._index.ntotal)
        except Exception as exc:
            raise IndexUnavailable(
                "Vector index is missing or corrupt.",
                suggestion="Open Settings > Indexes and rebuild the index.",
            ) from exc
        if self._index.d != self.dim:
            raise IndexUnavailable(
                f"Vector index dimension mismatch (index={self._index.d}, expected={self.dim}).",
                suggestion="Rebuild the index after changing the embedding model.",
            )

    # -- mutation --------------------------------------------------------
    def add(self, ids: Sequence[str], vectors: Sequence[Sequence[float]]) -> None:
        if not ids:
            return
        new_vecs = normalize(np.asarray(vectors, dtype=np.float32).reshape(len(ids), self.dim))
        existing = {id_: i for i, id_ in enumerate(self._ids)}
        drop_ids: list[str] = [id_ for id_ in ids if id_ in existing]
        if drop_ids:
            self.remove(drop_ids)
        self._ids.extend(ids)
        self._matrix = (
            np.vstack([self._matrix, new_vecs]) if self._matrix.size else new_vecs
        )
        self._rebuild_index()

    def remove(self, ids: Sequence[str]) -> None:
        if not ids:
            return
        drop = set(ids)
        keep = [i for i, id_ in enumerate(self._ids) if id_ not in drop]
        self._ids = [self._ids[i] for i in keep]
        self._matrix = self._matrix[keep] if keep else np.zeros((0, self.dim), dtype=np.float32)
        self._rebuild_index()

    # -- query -----------------------------------------------------------
    def query(self, vector: Sequence[float], top_k: int) -> list[VectorHit]:
        if not self._ids:
            return []
        query_vec = normalize(np.asarray(vector, dtype=np.float32).reshape(1, self.dim))
        scores, indices = self._index.search(query_vec, min(top_k, len(self._ids)))
        hits: list[VectorHit] = []
        for score, idx in zip(scores[0], indices[0], strict=True):
            if idx < 0 or idx >= len(self._ids):
                continue
            hits.append(VectorHit(id=self._ids[int(idx)], score=float(score)))
        return hits

    def count(self) -> int:
        return self._index.ntotal

    def ids(self) -> list[str]:
        return list(self._ids)
