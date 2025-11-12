import os
from functools import lru_cache
from typing import List

class Settings:
    """Application configuration from environment variables"""

    def __init__(self) -> None:
        self.setlistfm_base: str = os.getenv("SETLISTFM_BASE", "https://api.setlist.fm/rest/1.0")
        self.setlistfm_api_key: str = os.getenv("SETLISTFM_API_KEY", "")
        allowed = os.getenv(
            "API_ALLOWED_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173",
        )
        self.api_allowed_origins: List[str] = [origin.strip() for origin in allowed.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
