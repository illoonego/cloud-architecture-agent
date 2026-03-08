import json
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

from src.config.secrets_manager import get_secret


PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
    )

    # --- App ---
    PROJECT_NAME: str = "Cloud Architecture Agent"
    API_V1_STR: str = "/api/v1"

    # --- LLM / vLLM ---
    # vLLM OpenAI-compatible base URL
    # Override with .env file: VLLM_API_URL=http://YOUR_ELASTIC_IP:8000/v1
    # Use Elastic IP for stable address that won't change on EC2 stop/start
    VLLM_API_URL: str = "http://localhost:8000/v1"
    MODEL_NAME: str = "Qwen/Qwen2.5-3B-Instruct"

    # --- RAG / Qdrant ---
    # Local dev: ":memory:" for in-process Qdrant
    # Prod: e.g. "http://localhost:6333" or Qdrant Cloud URL
    QDRANT_URL: str = "http://localhost:6333"

    # Correct HF model id for SentenceTransformers MiniLM
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

    # Default number of chunks to retrieve
    RAG_TOP_K: int = 3

    # --- Authentication / AWS Secrets Manager ---
    # API keys are loaded from the secret defined below.
    AWS_SECRET_NAME: str = ""
    AWS_REGION: str = "us-east-1"

    @staticmethod
    def _parse_api_keys(raw_keys: str) -> list[str]:
        """Parse comma-separated API keys into a list."""
        return [key.strip() for key in raw_keys.split(",") if key.strip()]

    @staticmethod
    def _extract_keys_from_secret(secret_raw: str) -> list[str]:
        """Extract API keys from SecretString as JSON or raw comma-separated text."""
        try:
            secret_data = json.loads(secret_raw)
        except json.JSONDecodeError:
            # Support non-JSON SecretString values like: "key1,key2"
            return Settings._parse_api_keys(secret_raw)

        if isinstance(secret_data, dict):
            secret_keys = secret_data.get("API_KEYS", "")
            if isinstance(secret_keys, list):
                return [str(key).strip() for key in secret_keys if str(key).strip()]
            if isinstance(secret_keys, str):
                return Settings._parse_api_keys(secret_keys)

        if isinstance(secret_data, list):
            return [str(key).strip() for key in secret_data if str(key).strip()]

        return []

    @property
    def api_keys_list(self) -> list[str]:
        """Resolve API keys from AWS Secrets Manager only."""
        if self.AWS_SECRET_NAME:
            try:
                secret_raw = get_secret(self.AWS_SECRET_NAME, self.AWS_REGION)
                return self._extract_keys_from_secret(secret_raw)
            except Exception as exc:
                # Propagate a clear runtime error; auth layer will surface this as 500.
                raise RuntimeError(
                    "Failed to load API keys from AWS Secrets Manager. "
                    "Verify AWS credentials, IAM permissions (secretsmanager:GetSecretValue), "
                    "AWS_SECRET_NAME, and AWS_REGION."
                ) from exc

        return []

settings = Settings()
