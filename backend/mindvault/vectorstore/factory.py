from __future__ import annotations

import logging

from mindvault.config import Settings
from mindvault.errors import IndexUnavailable
from mindvault.vectorstore.base import VectorStore
from mindvault.vectorstore.numpy_store import NumpyVectorStore

logger = logging.getLogger("mindvault.vectorstore")

INDEX_FILENAME = "index.npz"


def create_vector_store(settings: Settings, dim: int) -> VectorStore:
    """Create and load the vector store, preferring FAISS when available."""
    path = settings.index_path / INDEX_FILENAME
    try:
        from mindvault.vectorstore.faiss_store import FaissVectorStore

        store: VectorStore = FaissVectorStore(path, dim)
    except IndexUnavailable:
        logger.warning("FAISS unavailable; using NumPy vector store.")
        store = NumpyVectorStore(path, dim)

    try:
        store.load()
    except IndexUnavailable:
        logger.warning("Vector index could not be loaded; starting empty.")
        store.save()
    return store
