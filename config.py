import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    BOT_TOKEN: str = os.getenv("BOT_TOKEN")
    FIRECRAWL_API_KEY: str = os.getenv("FIRECRAWL_API_KEY")
    MAX_RESULTS: int = int(os.getenv("MAX_RESULTS", 5))
    ENABLED_SOURCES: list = os.getenv("ENABLED_SOURCES", "hh.ru,getmatch.ru,geekjob.ru").split(",")

settings = Settings()
