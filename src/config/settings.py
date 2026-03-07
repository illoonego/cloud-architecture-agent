from pydantic_settings import BaseSettings


class Settings(BaseSettings):
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

    # --- Authentication ---
    # Comma-separated API keys from .env
    API_KEYS: str = ""

    @property
    def api_keys_list(self) -> list[str]:
        """Parse comma-separated API keys into a list."""
        if not self.API_KEYS:
            return []
        return [key.strip() for key in self.API_KEYS.split(",") if key.strip()]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
