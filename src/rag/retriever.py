# src/rag/retriever.py

from __future__ import annotations

import logging
from functools import lru_cache

from qdrant_client import QdrantClient

from src.config.settings import settings
from src.rag.embeddings import get_embedding_service

logger = logging.getLogger(__name__)


class ArchitectureRetriever:
    """
    Service responsible for searching the vector database (Qdrant).
    """

    def __init__(self, client: QdrantClient | None = None) -> None:
        # Local mode or remote depending on QDRANT_URL
        self.client = client or QdrantClient(location=settings.QDRANT_URL)
        self.embedding_service = get_embedding_service()
        self.collection_name = "aws_docs"

    def search(self, query: str, limit: int | None = None) -> list[str]:
        """
        Find the most relevant text chunks for a given query.
        Returns a list of text snippets.
        """
        if limit is None:
            limit = settings.RAG_TOP_K

        # 1. Convert query to vector
        query_vector = self.embedding_service.encode(query)

        # 2. Search Qdrant using query_points (compatible with current version)
        try:
            results_obj = self.client.query_points(
                collection_name=self.collection_name,
                query=query_vector,
                limit=limit,
            )
            hits = results_obj.points
        except Exception as e:
            logger.error(f"Error searching Qdrant: {e}")
            return []

        # 3. Extract text from payload
        results: list[str] = []
        for hit in hits:
            payload = hit.payload or {}
            text = payload.get("text")
            if text:
                results.append(text)

        return results


@lru_cache
def get_retriever() -> ArchitectureRetriever:
    """
    Singleton retriever so we don't recreate QdrantClient/EmbeddingService every call.
    """
    return ArchitectureRetriever()
