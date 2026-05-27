import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    FIRECRAWL_API_KEY: str = os.getenv("FIRECRAWL_API_KEY", "")

    MAX_RESULTS: int = int(os.getenv("MAX_RESULTS", "5"))
    ENABLED_SOURCES: list[str] = [
        s.strip()
        for s in os.getenv("ENABLED_SOURCES", "hh.ru,getmatch.ru,geekjob.ru").split(",")
        if s.strip()
    ]


settings = Settings()
