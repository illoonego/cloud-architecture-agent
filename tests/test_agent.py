"""
tests/test_agent.py

Unit tests for the AgentRouter class.
"""

from unittest.mock import patch

from src.agent.router import AgentRouter


class TestAgentRouter:
    """Test suite for AgentRouter."""

    def test_router_initialization(self):
        """Test that AgentRouter can be initialized."""
        router = AgentRouter()
        assert router is not None
        assert hasattr(router, "llm")
        assert hasattr(router, "query")

    def test_router_with_mock_llm(self, mock_llm_client):
        """Test AgentRouter with a mock LLM client."""
        router = AgentRouter(llm_client=mock_llm_client)
        assert router.llm == mock_llm_client

    @patch("src.agent.router.search_documentation")
    def test_query_with_context(self, mock_search, mock_llm_client, sample_query, sample_context):
        """Test query method when RAG returns context."""
        # Setup mocks
        mock_search.return_value = sample_context
        router = AgentRouter(llm_client=mock_llm_client)

        # Execute
        result = router.query(sample_query)

        # Verify
        assert result == "This is a test response from the LLM."
        mock_search.assert_called_once_with(sample_query)
        mock_llm_client.generate.assert_called_once()

        # Check that prompt includes context
        call_args = mock_llm_client.generate.call_args[0][0]
        assert "Context:" in call_args
        assert sample_context[0] in call_args

    @patch("src.agent.router.search_documentation")
    def test_query_without_context(self, mock_search, mock_llm_client, sample_query):
        """Test query method when RAG returns no context."""
        # Setup mocks
        mock_search.return_value = []
        router = AgentRouter(llm_client=mock_llm_client)

        # Execute
        result = router.query(sample_query)

        # Verify
        assert result == "This is a test response from the LLM."
        mock_search.assert_called_once_with(sample_query)
        mock_llm_client.generate.assert_called_once()

        # Check that prompt doesn't include context section
        call_args = mock_llm_client.generate.call_args[0][0]
        assert "Context:" not in call_args

    def test_query_prompt_structure(self, mock_llm_client, sample_query):
        """Test that query constructs proper prompt structure."""
        with patch("src.agent.router.search_documentation", return_value=[]):
            router = AgentRouter(llm_client=mock_llm_client)
            router.query(sample_query)

            # Get the prompt passed to LLM
            call_args = mock_llm_client.generate.call_args[0][0]

            # Verify prompt structure
            assert "AWS Cloud Architecture expert" in call_args
            assert sample_query in call_args
            assert "Answer:" in call_args
