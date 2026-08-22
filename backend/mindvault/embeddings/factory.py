from __future__ import annotations

import logging

from mindvault.config import Settings
from mindvault.embeddings.base import EmbeddingProvider
from mindvault.embeddings.hash_embedding import HashEmbeddingProvider

logger = logging.getLogger("mindvault.embeddings")


def create_embedding_provider(settings: Settings) -> EmbeddingProvider:
    """Pick the embedding provider.

    Priority:
      1. explicit ``MV_EMBEDDING_PROVIDER`` choice
      2. sentence-transformers when ``mindvault[ml]`` is installed
      3. deterministic hash fallback (works everywhere, no download)
    """
    configured = settings.embedding_provider.strip().lower()
    if configured == "hash":
        return HashEmbeddingProvider(dim=settings.embedding_dim)

    if configured in ("auto", "sentence-transformers", "st"):
        try:
            from mindvault.embeddings.sentence_transformer import SentenceTransformerProvider

            provider = SentenceTransformerProvider(settings.embedding_model, dim=settings.embedding_dim)
            return provider
        except ImportError:
            if configured != "auto":
                raise
            logger.warning("sentence-transformers not installed; using deterministic hash embeddings.")
            return HashEmbeddingProvider(dim=settings.embedding_dim)
    raise ValueError(f"Unknown embedding provider: {configured}")
