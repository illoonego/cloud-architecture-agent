# src/llm/client.py

import logging

import openai
from openai import APIConnectionError, APITimeoutError

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

        Raises:
            APITimeoutError: If LLM server doesn't respond in time
            APIConnectionError: If cannot connect to LLM server
            Exception: For other LLM errors
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
            content = response.choices[0].message.content
            return content or ""
        except (APITimeoutError, APIConnectionError) as e:
            logger.error(f"LLM service unavailable: {type(e).__name__}: {e}")
            # Re-raise to let FastAPI handle with proper status code
            raise
        except Exception as e:
            logger.error(f"Error calling LLM: {type(e).__name__}: {e}")
            import traceback

            logger.error(traceback.format_exc())
            # Re-raise to let FastAPI handle
            raise
