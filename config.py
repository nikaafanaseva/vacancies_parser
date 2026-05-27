import os
from dotenv import load_dotenv

# Загружает .env если запускаешь локально. На Railway берёт переменные окружения автоматически.
load_dotenv()

class Settings:
    BOT_TOKEN: str = os.getenv("BOT_TOKEN")
    DEVELOPER_EMAIL: str = os.getenv("DEVELOPER_EMAIL", "dev@example.com")
    REQUEST_DELAY: float = float(os.getenv("REQUEST_DELAY", 2.0))
    MAX_RESULTS: int = int(os.getenv("MAX_RESULTS", 10))
    ENABLED_SOURCES: list = os.getenv("ENABLED_SOURCES", "hh.ru,getmatch.ru,geekjob.ru").split(",")

settings = Settings()
