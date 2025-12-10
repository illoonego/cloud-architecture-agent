"""
tests/test_rag.py

Unit tests for RAG components (retriever and embeddings).
"""

from unittest.mock import Mock, patch

from src.rag.retriever import ArchitectureRetriever


class TestArchitectureRetriever:
    """Test suite for ArchitectureRetriever."""

    def test_retriever_initialization(self, mock_qdrant_client):
        """Test that retriever can be initialized with mock client."""
        retriever = ArchitectureRetriever(client=mock_qdrant_client)
        assert retriever is not None
        assert retriever.client == mock_qdrant_client
        assert retriever.collection_name == "aws_docs"

    @patch('src.rag.retriever.get_embedding_service')
    def test_search_basic(self, mock_get_embedding, mock_qdrant_client, sample_query):
        """Test basic search functionality."""
        # Setup mocks
        mock_embedding_service = Mock()
        mock_embedding_service.encode.return_value = [0.1] * 384
        mock_get_embedding.return_value = mock_embedding_service

        # Create retriever
        retriever = ArchitectureRetriever(client=mock_qdrant_client)

        # Execute search
        results = retriever.search(sample_query, limit=2)

        # Verify
        assert isinstance(results, list)
        assert len(results) == 2
        assert "AWS VPC" in results[0]
        assert "EC2" in results[1]

        # Verify embedding service was called
        mock_embedding_service.encode.assert_called_once_with(sample_query)

        # Verify Qdrant was queried
        mock_qdrant_client.query_points.assert_called_once()

    @patch('src.rag.retriever.get_embedding_service')
    def test_search_with_custom_limit(self, mock_get_embedding, mock_qdrant_client, sample_query):
        """Test search with custom result limit."""
        # Setup mocks
        mock_embedding_service = Mock()
        mock_embedding_service.encode.return_value = [0.1] * 384
        mock_get_embedding.return_value = mock_embedding_service

        retriever = ArchitectureRetriever(client=mock_qdrant_client)

        # Search with custom limit
        retriever.search(sample_query, limit=5)

        # Verify limit was passed to query_points
        call_kwargs = mock_qdrant_client.query_points.call_args[1]
        assert call_kwargs['limit'] == 5

    @patch('src.rag.retriever.get_embedding_service')
    def test_search_exception_handling(self, mock_get_embedding, sample_query):
        """Test that search handles Qdrant exceptions gracefully."""
        # Setup mocks
        mock_embedding_service = Mock()
        mock_embedding_service.encode.return_value = [0.1] * 384
        mock_get_embedding.return_value = mock_embedding_service

        # Mock Qdrant client that raises exception
        mock_client = Mock()
        mock_client.query_points.side_effect = Exception("Connection error")

        retriever = ArchitectureRetriever(client=mock_client)

        # Execute search (should not raise, should return empty list)
        results = retriever.search(sample_query)

        # Verify graceful handling
        assert results == []

    @patch('src.rag.retriever.get_embedding_service')
    def test_search_uses_default_top_k(self, mock_get_embedding, mock_qdrant_client, sample_query):
        """Test that search uses settings.RAG_TOP_K when limit not specified."""
        # Setup mocks
        mock_embedding_service = Mock()
        mock_embedding_service.encode.return_value = [0.1] * 384
        mock_get_embedding.return_value = mock_embedding_service

        retriever = ArchitectureRetriever(client=mock_qdrant_client)

        # Search without specifying limit
        retriever.search(sample_query)

        # Verify default limit was used (should be 3 from settings)
        call_kwargs = mock_qdrant_client.query_points.call_args[1]
        assert 'limit' in call_kwargs
        assert call_kwargs['limit'] == 3  # Default from settings


class TestEmbeddings:
    """Test suite for embedding functionality."""

    def test_embedding_import(self):
        """Test that embedding service can be imported."""
        from src.rag.embeddings import get_embedding_service
        assert get_embedding_service is not None

    def test_get_embedding_service_returns_instance(self):
        """Test that embedding service returns a valid instance."""
        from src.rag.embeddings import get_embedding_service

        # Get embedding service
        service = get_embedding_service()

        # Should return a valid instance
        assert service is not None
        assert hasattr(service, 'encode')
