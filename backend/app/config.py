from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = BACKEND_DIR.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(PROJECT_DIR / ".env", BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "PageStruct AI"
    debug: bool = True
    llm_api_key: Optional[str] = None
    llm_api_url: str = "https://api.openai.com/v1/chat/completions"
    llm_model: str = "gpt-4o-mini"
    llm_timeout: int = 60

    base_dir: Path = Path(__file__).resolve().parent
    templates_dir: Path = base_dir / "templates"
    static_dir: Path = base_dir / "static"


@lru_cache
def get_settings() -> Settings:
    return Settings()
