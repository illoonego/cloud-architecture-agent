# src/agent/router.py

from src.agent.tools import search_documentation
from src.llm.client import LLMClient


class AgentRouter:
    """
    The orchestrator that coordinates the LLM, RAG, and tools.
    """

    def __init__(self, llm_client: LLMClient | None = None):
        # Allow injection for tests, but default to real client
        self.llm = llm_client or LLMClient()

    def query(self, user_input: str) -> str:
        """
        Process a user query through the agent pipeline.
        """
        # 1) Search for relevant context using RAG
        context_chunks = search_documentation(user_input)

        # 2) Construct the prompt with context
        if context_chunks:
            context_text = "\n\n".join(context_chunks)
            prompt = (
                "You are an AWS Cloud Architecture expert. "
                "Use the following context to answer the user's question.\n\n"
                f"Context:\n{context_text}\n\n"
                f"User Question: {user_input}\n\n"
                "Answer:"
            )
        else:
            prompt = (
                "You are an AWS Cloud Architecture expert. "
                "Answer the user's question.\n\n"
                f"User Question: {user_input}\n\n"
                "Answer:"
            )

        # 3) Get response from LLM
        response = self.llm.generate(prompt)
        return response
