from functools import lru_cache
from pathlib import Path
from urllib.parse import quote_plus

from dotenv import dotenv_values

ENV_PATH = Path(__file__).resolve().parent.parent / ".env"


def _env(key: str, default: str | None = None) -> str:
    values = dotenv_values(ENV_PATH)
    value = values.get(key) or default
    if value is None:
        raise RuntimeError(f"Missing required environment variable: {key}")
    return value


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
