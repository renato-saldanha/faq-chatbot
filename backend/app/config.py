from functools import lru_cache
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from pydantic import field_validator
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

    cors_origins: str = "http://localhost:3000"
    cookie_secure: bool = True

    # Modo demonstração (ex.: deploy na Vercel): OTP stateless e código devolvido na resposta.
    demo_mode: bool = False

    @field_validator("database_url")
    @classmethod
    def normalize_database_url(cls, v: str) -> str:
        """Aceita a URL no formato do provedor (postgres://...?sslmode=require) e a adapta ao asyncpg."""
        url = urlsplit(v)
        scheme = url.scheme
        if scheme in ("postgres", "postgresql"):
            scheme = "postgresql+asyncpg"
        query = []
        for key, value in parse_qsl(url.query, keep_blank_values=True):
            if key == "sslmode":
                query.append(("ssl", value))
            elif key not in ("channel_binding",):
                query.append((key, value))
        return urlunsplit((scheme, url.netloc, url.path, urlencode(query), url.fragment))

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
