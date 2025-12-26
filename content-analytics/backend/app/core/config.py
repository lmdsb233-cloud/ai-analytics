from pydantic_settings import BaseSettings
from typing import Optional
from functools import lru_cache
from urllib.parse import urlsplit, urlunsplit

from pydantic import field_validator


def _normalize_localhost(url: str) -> str:
    """Windows 下 localhost 可能先解析到 IPv6 (::1)，导致连接回退等待 ~20s。

    将 host=localhost 归一化为 127.0.0.1，避免每次建连都产生固定延迟。
    """
    try:
        parts = urlsplit(url)
        if parts.hostname != "localhost":
            return url

        netloc = parts.netloc.replace("localhost", "127.0.0.1")
        return urlunsplit((parts.scheme, netloc, parts.path, parts.query, parts.fragment))
    except Exception:
        return url


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Content Analytics API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@127.0.0.1:5433/content_analytics"
    
    # Redis
    REDIS_URL: str = "redis://127.0.0.1:6380/0"
    
    # Security
    SECRET_KEY: str = "your-super-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    
    # AI Provider
    AI_PROVIDER: str = "deepseek"  # deepseek or openai
    DEEPSEEK_API_KEY: Optional[str] = None
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com/v1"
    OPENAI_API_KEY: Optional[str] = None
    
    # File Upload
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB

    @field_validator("DATABASE_URL", "REDIS_URL", mode="before")
    @classmethod
    def _normalize_service_urls(cls, v):
        if isinstance(v, str):
            return _normalize_localhost(v)
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
