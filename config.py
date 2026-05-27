from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    BOT_TOKEN: str = Field(..., description="Telegram bot token")
    FIRECRAWL_API_KEY: str = Field(..., description="Firecrawl API key")
    MAX_RESULTS: int = Field(default=5, description="Max results per source")
    ENABLED_SOURCES: list = Field(default=["hh.ru", "getmatch.ru", "geekjob.ru"])

    class Config:
        env_file = ".env"

settings = Settings()
