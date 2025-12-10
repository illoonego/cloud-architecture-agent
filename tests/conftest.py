"""
tests/conftest.py

Pytest fixtures and configuration for the test suite.
"""

from unittest.mock import MagicMock, Mock

import pytest


@pytest.fixture
def mock_llm_client():
    """Mock LLM client for testing without external dependencies."""
    mock_client = Mock()
    mock_client.generate.return_value = "This is a test response from the LLM."
    return mock_client


@pytest.fixture
def mock_qdrant_client():
    """Mock Qdrant client for testing without vector database."""
    mock_client = Mock()

    # Mock query_points response
    mock_result = MagicMock()
    mock_result.points = [
        MagicMock(payload={"text": "AWS VPC is a virtual network."}),
        MagicMock(payload={"text": "EC2 provides scalable compute capacity."}),
    ]
    mock_client.query_points.return_value = mock_result

    return mock_client


@pytest.fixture
def mock_embedding_service():
    """Mock embedding service for testing."""
    mock_service = Mock()
    mock_service.encode.return_value = [0.1] * 384  # Fake embedding vector
    return mock_service


@pytest.fixture
def sample_query():
    """Sample user query for testing."""
    return "What is AWS VPC?"


@pytest.fixture
def sample_context():
    """Sample context chunks for testing."""
    return [
        "AWS VPC is a virtual private cloud service.",
        "You can launch AWS resources in a logically isolated virtual network.",
    ]
