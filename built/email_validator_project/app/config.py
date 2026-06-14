import os

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite+aiosqlite:///./dev.db")
SECRET_KEY = os.environ.get("SECRET_KEY", "change-me")
