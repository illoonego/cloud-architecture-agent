# src/rag/embeddings.py

from functools import lru_cache

from sentence_transformers import SentenceTransformer

from src.config.settings import settings


class EmbeddingService:
    """
    Service responsible for converting text into vectors (embeddings).
    """

    def __init__(self):
        try:
            print(f"[embeddings] Loading model: {settings.EMBEDDING_MODEL}...")
            self.encoder = SentenceTransformer(settings.EMBEDDING_MODEL)
        except Exception as e:
            raise RuntimeError(
                f"Failed to load embedding model '{settings.EMBEDDING_MODEL}': {e}"
            ) from e

    def encode(self, text: str) -> list[float]:
        """
        Convert a single string into a vector.
        """
        return self.encoder.encode(text).tolist()

    def encode_batch(self, texts: list[str]) -> list[list[float]]:
        """
        Convert a list of strings into a list of vectors.
        """
        return self.encoder.encode(texts).tolist()


@lru_cache
def get_embedding_service() -> EmbeddingService:
    """
    Singleton factory. Returns the same instance of EmbeddingService every time.
    """
    return EmbeddingService()
