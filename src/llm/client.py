# src/llm/client.py

import logging

import openai

from src.config.settings import settings

logger = logging.getLogger(__name__)


class LLMClient:
    """
    A client to talk to a vLLM server (OpenAI-compatible API).
    """

    def __init__(self):
        # vLLM usually doesn't require a real key; "EMPTY" is standard.
        self.client = openai.OpenAI(
            base_url=settings.VLLM_API_URL,
            api_key="EMPTY",
            timeout=60.0,
        )
        self.model = settings.MODEL_NAME

    def generate(self, prompt: str) -> str:
        """
        Send a prompt to the LLM and return the text answer.
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful AWS Cloud Architect assistant.",
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
                temperature=0.7,
                max_tokens=512,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error calling LLM: {type(e).__name__}: {e}")
            import traceback

            logger.error(traceback.format_exc())
            return f"Error: Could not connect to the LLM server. {type(e).__name__}: {str(e)}"
