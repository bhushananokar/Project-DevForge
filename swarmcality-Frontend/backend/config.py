from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_REPO_ROOT = Path(__file__).resolve().parents[2]
_BACKEND_DIR = Path(__file__).resolve().parent


class Settings(BaseSettings):
    OPENAI_API_KEY: str
    MONGODB_URL: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "promptforge"
    SECRET_KEY: str = "change-me-in-production-use-openssl-rand-hex-32"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    CORS_ORIGINS: str = "http://localhost:3000"

    model_config = SettingsConfigDict(
        env_file=(
            str(_BACKEND_DIR / ".env"),
            str(_REPO_ROOT / ".env"),
        ),
        extra="ignore",
    )


settings = Settings()
