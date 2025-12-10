# src/agent/tools.py

from src.rag.retriever import get_retriever


def search_documentation(query: str) -> list[str]:
    """
    Search the AWS architecture documentation for relevant information.

    Args:
        query: The search query.

    Returns:
        List of relevant text chunks.
    """
    retriever = get_retriever()
    return retriever.search(query)
