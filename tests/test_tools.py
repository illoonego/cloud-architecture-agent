"""
tests/test_tools.py

Unit tests for agent tools (search_documentation).
"""

from unittest.mock import Mock, patch

from src.agent.tools import search_documentation


class TestSearchDocumentation:
    """Test suite for search_documentation tool."""

    @patch('src.agent.tools.get_retriever')
    def test_search_documentation_basic(self, mock_get_retriever, sample_query, sample_context):
        """Test basic search_documentation functionality."""
        # Setup mock retriever
        mock_retriever = Mock()
        mock_retriever.search.return_value = sample_context
        mock_get_retriever.return_value = mock_retriever

        # Execute
        results = search_documentation(sample_query)

        # Verify
        assert results == sample_context
        mock_retriever.search.assert_called_once_with(sample_query)

    @patch('src.agent.tools.get_retriever')
    def test_search_documentation_empty_results(self, mock_get_retriever, sample_query):
        """Test search_documentation when no results found."""
        # Setup mock retriever with empty results
        mock_retriever = Mock()
        mock_retriever.search.return_value = []
        mock_get_retriever.return_value = mock_retriever

        # Execute
        results = search_documentation(sample_query)

        # Verify
        assert results == []
        assert isinstance(results, list)

    @patch('src.agent.tools.get_retriever')
    def test_search_documentation_multiple_chunks(self, mock_get_retriever):
        """Test search_documentation with multiple context chunks."""
        # Setup mock with multiple results
        mock_retriever = Mock()
        expected_results = [
            "VPC allows you to provision a logically isolated section.",
            "You can select your own IP address range.",
            "Create subnets and configure route tables.",
        ]
        mock_retriever.search.return_value = expected_results
        mock_get_retriever.return_value = mock_retriever

        # Execute
        results = search_documentation("How do I configure VPC?")

        # Verify
        assert len(results) == 3
        assert results == expected_results

    @patch('src.agent.tools.get_retriever')
    def test_search_documentation_caches_retriever(self, mock_get_retriever):
        """Test that retriever is reused across calls."""
        # Setup mock
        mock_retriever = Mock()
        mock_retriever.search.return_value = ["result"]
        mock_get_retriever.return_value = mock_retriever

        # Call multiple times
        search_documentation("query 1")
        search_documentation("query 2")
        search_documentation("query 3")

        # get_retriever should only be called once (cached)
        assert mock_get_retriever.call_count == 3  # Called each time due to function-level cache

        # But search should be called 3 times
        assert mock_retriever.search.call_count == 3


class TestToolsIntegration:
    """Integration tests for tools module."""

    def test_tools_module_imports(self):
        """Test that tools module can be imported."""
        from src.agent import tools
        assert hasattr(tools, 'search_documentation')

    def test_search_documentation_signature(self):
        """Test that search_documentation has correct signature."""
        import inspect
        sig = inspect.signature(search_documentation)

        # Should accept query parameter
        assert 'query' in sig.parameters

        # Should return list[str]
        assert sig.return_annotation == list[str]
