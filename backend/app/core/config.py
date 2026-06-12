"""
Enterprise RAG Platform Configuration
Manages environment-based settings for multi-tenant deployment.
"""

from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings using environment variables.
    Supports multi-environment deployment (dev, staging, prod).
    """

    # ==================== App Configuration ====================
    APP_NAME: str = "Enterprise RAG Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # ==================== API Configuration ====================
    API_V1_STR: str = "/api/v1"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8080"]
    ALLOWED_HOSTS: list[str] = ["*"]

    # ==================== Database Configuration ====================
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/enterprise_rag"
    DATABASE_ECHO: bool = False
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10

    # ==================== Redis Configuration ====================
    REDIS_URL: str = "redis://localhost:6379/0"
    CACHE_TTL_SECONDS: int = 3600

    # ==================== Celery Configuration ====================
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # ==================== OpenTelemetry Configuration ====================
    OTEL_ENABLED: bool = True
    OTEL_EXPORTER_OTLP_ENDPOINT: str = "http://localhost:4317"
    OTEL_EXPORTER_OTLP_TRACES_ENDPOINT: str = "http://localhost:4317/v1/traces"
    OTEL_EXPORTER_OTLP_METRICS_ENDPOINT: str = "http://localhost:4317/v1/metrics"
    OTEL_SERVICE_NAME: str = "enterprise-rag-api"
    OTEL_SERVICE_VERSION: str = "1.0.0"
    OTEL_SAMPLE_RATE: float = 1.0  # Sample 100% of traces in production, adjust to 0.1 for 10%

    # ==================== Vector Store Configuration ====================
    VECTOR_STORE_TYPE: str = "faiss"  # faiss | pinecone
    VECTOR_STORE_PATH: str = "./data/vector_store"
    VECTOR_DIMENSION: int = 384
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 50

    # ==================== LLM Configuration ====================
    LLM_PROVIDER: str = "openai"  # openai | anthropic | deepseek
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4-turbo-preview"
    TEMPERATURE: float = 0.7
    MAX_TOKENS: int = 2048

    # ==================== LLM-as-Judge Configuration ====================
    JUDGE_MODEL: str = "gpt-4-turbo-preview"  # Cheaper model for evaluation
    JUDGE_ENABLED: bool = True
    JUDGE_SAMPLE_RATE: float = 0.1  # Evaluate 10% of production traces

    # ==================== Multi-Tenancy & RBAC ====================
    ENABLE_MULTI_TENANCY: bool = True
    ENABLE_RBAC: bool = True
    DEFAULT_TENANT: str = "default"

    # ==================== A/B Testing Configuration ====================
    AB_TESTING_ENABLED: bool = True
    AB_TEST_VARIANTS: dict = {
        "variant_a": {
            "chunk_size": 512,
            "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
        },
        "variant_b": {
            "chunk_size": 1024,
            "embedding_model": "sentence-transformers/all-mpnet-base-v2",
        },
    }

    # ==================== Security Configuration ====================
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ENABLE_API_KEYS: bool = True

    # ==================== Logging Configuration ====================
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
