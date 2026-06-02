import os
from functools import lru_cache
from pathlib import Path
from urllib.parse import quote_plus, urlparse

from dotenv import dotenv_values

ENV_PATH = Path(__file__).resolve().parent.parent / ".env"


@lru_cache
def _file_env() -> dict[str, str | None]:
    return dotenv_values(ENV_PATH)


def _lookup_env(key: str) -> str | None:
    value = os.environ.get(key)
    if value:
        return value
    file_value = _file_env().get(key)
    return file_value if file_value else None


def _env(key: str, default: str | None = None) -> str:
    value = _lookup_env(key) or default
    if value is None:
        raise RuntimeError(f"Missing required environment variable: {key}")
    return value


def _env_optional(key: str) -> str | None:
    return _lookup_env(key)


_DEFAULT_CORS_ORIGINS = (
    "http://localhost:5173",
    "http://127.0.0.1:5173",
)


def normalize_origin(url: str) -> str:
    trimmed = url.strip().rstrip("/")
    if not trimmed:
        raise RuntimeError("FRONTEND_URL must not be empty")
    parsed = urlparse(trimmed if "://" in trimmed else f"https://{trimmed}")
    if not parsed.scheme or not parsed.netloc:
        raise RuntimeError(f"Invalid FRONTEND_URL: {url!r}")
    return f"{parsed.scheme}://{parsed.netloc}"


def build_cors_origins(
    frontend_url: str | None,
    cors_origins_raw: str | None,
) -> list[str]:
    origins: list[str] = []
    seen: set[str] = set()

    def add(origin: str) -> None:
        normalized = origin.strip().rstrip("/")
        if normalized and normalized not in seen:
            seen.add(normalized)
            origins.append(normalized)

    if frontend_url:
        add(normalize_origin(frontend_url))

    if cors_origins_raw:
        for part in cors_origins_raw.split(","):
            add(part)

    if origins:
        return origins
    return list(_DEFAULT_CORS_ORIGINS)


@lru_cache
def get_settings() -> "Settings":
    return Settings()


class Settings:
    def __init__(self) -> None:
        self.host = _env("HOST")
        self.port = int(_env("PORT", "5432"))
        self.user = _env("USER")
        self.password = _env("PASSWORD")
        self.database = _env("DATABASE", "weightloss")
        self.openai_api_key = _env("OPENAI_API_KEY")
        self.openai_model = _env("OPENAI_MODEL", "gpt-5.4")
        frontend_url = _env_optional("FRONTEND_URL")
        self.frontend_origin = (
            normalize_origin(frontend_url) if frontend_url else None
        )
        self.cors_origins = build_cors_origins(
            frontend_url,
            _env_optional("CORS_ORIGINS"),
        )

    def _credentials(self) -> str:
        return (
            f"{quote_plus(self.user)}:{quote_plus(self.password)}"
            f"@{self.host}:{self.port}"
        )

    @property
    def database_url(self) -> str:
        return f"postgresql+psycopg://{self._credentials()}/{self.database}"

    @property
    def admin_database_url(self) -> str:
        return f"postgresql+psycopg://{self._credentials()}/postgres"
