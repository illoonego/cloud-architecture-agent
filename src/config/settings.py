# src/config/settings.py

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # --- App ---
    PROJECT_NAME: str = "Cloud Architecture Agent"
    API_V1_STR: str = "/api/v1"

    # --- LLM / vLLM ---
    # vLLM OpenAI-compatible base URL
    # Override with .env file: VLLM_API_URL=http://YOUR_EC2_IP:8000/v1
    VLLM_API_URL: str = "http://localhost:8000/v1"
    MODEL_NAME: str = "meta-llama/Llama-3.1-8B-Instruct"

    # --- RAG / Qdrant ---
    # Local dev: ":memory:" for in-process Qdrant
    # Prod: e.g. "http://localhost:6333" or Qdrant Cloud URL
    QDRANT_URL: str = "http://localhost:6333"

    # Correct HF model id for SentenceTransformers MiniLM
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

    # Default number of chunks to retrieve
    RAG_TOP_K: int = 3

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
