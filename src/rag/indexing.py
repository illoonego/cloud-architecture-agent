# src/rag/indexing.py

import logging
import uuid

from qdrant_client import QdrantClient
from qdrant_client.http import models

from src.config.settings import settings
from src.rag.embeddings import get_embedding_service

logger = logging.getLogger(__name__)

class Indexer:
    """
    Service responsible for indexing documents into the vector database (Qdrant).
    """

    def __init__(self, client: QdrantClient | None = None):
        # Local mode (":memory:") for dev OR a URL for real Qdrant
        self.client = client or QdrantClient(location=settings.QDRANT_URL)
        self.embedding_service = get_embedding_service()
        self.collection_name = "aws_docs"
        self._ensure_collection()

    def _ensure_collection(self) -> None:
        """
        Make sure the collection exists in Qdrant.
        """
        try:
            if not self.client.collection_exists(self.collection_name):
                # 384 is correct for MiniLM-L6-v2
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=models.VectorParams(
                        size=384,
                        distance=models.Distance.COSINE,
                    ),
                )
        except Exception as e:
            logger.error(f"Error ensuring Qdrant collection: {e}")

    def index_documents(self, documents: list[str]) -> None:
        """
        Add a list of text documents to the database.

        Each element in `documents` is considered a separate chunk.
        You can implement more advanced chunking upstream.
        """
        if not documents:
            return

        try:
            # 1. Convert text to vectors
            vectors = self.embedding_service.encode_batch(documents)

            # 2. Prepare points for Qdrant
            points: list[models.PointStruct] = []
            for i, doc in enumerate(documents):
                points.append(
                    models.PointStruct(
                        id=str(uuid.uuid4()),
                        vector=vectors[i],
                        payload={"text": doc},
                    )
                )

            # 3. Upload
            self.client.upsert(
                collection_name=self.collection_name,
                points=points,
            )
        except Exception as e:
            logger.error(f"Error indexing documents in Qdrant: {e}")
