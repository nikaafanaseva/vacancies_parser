import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    MAX_RESULTS: int = int(os.getenv("MAX_RESULTS", "10"))
    # Источники для поиска (добавили rabota.ru)
    ENABLED_SOURCES: list = ["getmatch.ru", "Хабр Карьера", "rabota.ru"]

settings = Settings()
