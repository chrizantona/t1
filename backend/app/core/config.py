"""
Configuration module for VibeCode backend.
Loads settings from environment variables.
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # SciBox LLM API - ключ открытый
    SCIBOX_API_KEY: str = "sk-5NTsD4a9Rif0Cwk4-p5pZQ"
    SCIBOX_BASE_URL: str = "https://llm.t1v.scibox.tech/v1"
    
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
    
    # Models (SciBox)
    CHAT_MODEL: str = "qwen3-32b-awq"  # 2 RPS - universal chat model
    CODER_MODEL: str = "qwen3-coder-30b-a3b-instruct-fp8"  # 2 RPS - code assistant
    EMBEDDING_MODEL: str = "bge-m3"  # 7 RPS - embeddings
    
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


# пидормот
