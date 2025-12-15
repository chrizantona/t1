"""
Configuration module for VibeCode backend.
Loads settings from environment variables.
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Cloud.ru LLM API
    SCIBOX_API_KEY: str = "ZjdkMmViNmYtNzBjNC00ZjJiLWI1MWYtNTNhMGRmOTQwZWQ2.3903d49de8fb6acef2bb178bea104a70"
    SCIBOX_BASE_URL: str = "https://foundation-models.api.cloud.ru/v1"
    
    # Database
    POSTGRES_USER: str = "vibecode"
    POSTGRES_PASSWORD: str = "vibecode"
    POSTGRES_DB: str = "vibecode"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5433
    DATABASE_URL: str = "postgresql+psycopg://vibecode:vibecode@postgres:5432/vibecode"
    
    # Backend
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    
    # CORS
    FRONTEND_ORIGIN: str = "http://localhost:5173"
    
    # Models (Cloud.ru)
    CHAT_MODEL: str = "Qwen/Qwen3-235B-A22B-Instruct-2507"  # universal chat model
    CODER_MODEL: str = "Qwen/Qwen3-Coder-480B-A35B-Instruct"  # code assistant
    EMBEDDING_MODEL: str = "BAAI/bge-m3"  # embeddings
    
    # Rate limits (requests per second)
    CHAT_MODEL_RPS: int = 2
    CODER_MODEL_RPS: int = 2
    EMBEDDING_MODEL_RPS: int = 7
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"


settings = Settings()

