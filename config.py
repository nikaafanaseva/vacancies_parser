from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    BOT_TOKEN: str = Field(8832828282:AAGLQ3KPoZNX9VluDFiyGF3VlpqvzddeHT0, description="Telegram bot token")
    FIRECRAWL_API_KEY: str = Field(fc-9e80a939f6b54d6e9f2eebe0ef16bd55, description="Firecrawl API key")
    MAX_RESULTS: int = Field(default=5, description="Max results per source")
    ENABLED_SOURCES: list = Field(default=["hh.ru", "getmatch.ru", "geekjob.ru"])

    class Config:
        env_file = ".env"

settings = Settings()
