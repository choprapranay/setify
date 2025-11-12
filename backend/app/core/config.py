import os
from functools import lru_cache
from typing import List
from dotenv import load_dotenv

load_dotenv()

class Settings:
    """Application configuration from environment variables"""

    def __init__(self) -> None:
        self.setlistfm_base: str = os.getenv("SETLISTFM_BASE", "https://api.setlist.fm/rest/1.0")
        self.setlistfm_api_key: str = os.getenv("SETLISTFM_API_KEY", "")
        allowed = os.getenv(
            "API_ALLOWED_ORIGINS",
            "http://127.0.0.1:8000",
        )
        self.api_allowed_origins: List[str] = [origin.strip() for origin in allowed.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
