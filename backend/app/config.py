import os
from pydantic_settings import BaseSettings
from typing import List, Optional


class Settings(BaseSettings):
    anthropic_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    zendesk_url: str
    zendesk_email: str
    zendesk_api_token: str
    cors_origins: List[str] = ["http://localhost:5173", "http://localhost:3000"]
    llm_provider: str = "auto"  # "auto", "openai", or "anthropic"

    class Config:
        env_file = ".env"


settings = Settings()
