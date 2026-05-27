from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List

class Settings(BaseSettings):
    BOT_TOKEN: str = Field(..., description="Telegram bot token")
    FIRECRAWL_API_KEY: str = Field(..., description="Firecrawl API key")
    MAX_RESULTS: int = Field(default=5, description="Max results per source")
    
    # Читаем как простую строку через запятую — так надёжнее, чем JSON
    ENABLED_SOURCES: str = Field(default="hh.ru,getmatch.ru,geekjob.ru")

    def get_sources(self) -> List[str]:
        """Возвращает список источников, разбивая строку по запятым"""
        return [s.strip() for s in self.ENABLED_SOURCES.split(",") if s.strip()]

    class Config:
        env_file = ".env"

settings = Settings()
