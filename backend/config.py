from pydantic_settings import BaseSettings
from pathlib import Path
import os

BACKEND_DIR = Path(__file__).resolve().parent


class Settings(BaseSettings):
    APP_NAME: str = "FavAgent"
    DATABASE_URL: str = f"sqlite:///{BACKEND_DIR / 'favagent.db'}"
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    OPENAI_MODEL: str = "gpt-4o-mini"
    DEFAULT_REMINDER_DAYS: int = 3
    BACKEND_ROOT: Path = BACKEND_DIR

    class Config:
        env_file = str(BACKEND_DIR.parent / ".env")
        env_file_encoding = "utf-8"


settings = Settings()
