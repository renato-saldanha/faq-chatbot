from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://postgres:postgres@postgres:5432/faq_chatbot"

    similarity_backend: str = "fuzzy"
    similarity_threshold: float = 0.55

    openai_api_key: str = ""
    openai_model: str = "text-embedding-3-small"

    admin_email: str = "admin@example.com"
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""

    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 8


@lru_cache
def get_settings() -> Settings:
    return Settings()
