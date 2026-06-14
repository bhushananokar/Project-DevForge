from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    OPENAI_API_KEY: str
    MONGODB_URL: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "promptforge"
    SECRET_KEY: str = "change-me-in-production-use-openssl-rand-hex-32"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    CORS_ORIGINS: str = "http://localhost:3000"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
