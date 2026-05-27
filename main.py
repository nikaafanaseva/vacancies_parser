import asyncio
import logging
import os
import sys
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message

from config import settings
from parsers.hh_parser import HHParser
from parsers.getmatch_parser import GetMatchParser
from parsers.geekjob_parser import GeekJobParser
from utils import format_results, safe_format_query

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

if not settings.BOT_TOKEN:
    logger.error("BOT_TOKEN не установлен")
    sys.exit(1)

# Firecrawl API key нужен только для getmatch и geekjob.
# HH.ru использует бесплатный публичный API — ключ не нужен!

bot = Bot(token=settings.BOT_TOKEN)
dp = Dispatcher()

parsers = {
    "hh.ru": HHParser(),  # ← БЕЗ api_key!
    "getmatch.ru": GetMatchParser(api_key=settings.FIRECRAWL_API_KEY),
    "geekjob.ru": GeekJobParser(api_key=settings.FIRECRAWL_API_KEY),
}


@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "Бот поиска вакансий\n\n"
        "Команда:\n"
        "/search <запрос>\n\n"
        "Примеры:\n"
        "/search маркетинг\n"
        "/search python разработчик удаленно\n\n"
        "Источники: hh.ru (API), getmatch.ru, geekjob.ru"
    )


@dp.message(Command("search"))
async def cmd_search(message: Message):
    args = message.text.split(maxsplit=1)

    if len(args) < 2:
        await message.answer("Неверный формат. Используй: /search <запрос>")
        return

    query = safe_format_query(args[1])
    status_msg = await message.answer(f"Ищу вакансии по запросу: {query}")

    tasks = [
        parsers[source].search(query, limit=settings.MAX_RESULTS)
        for source in settings.ENABLED_SOURCES
        if source in parsers
    ]

    if not tasks:
        await status_msg.edit_text("Нет активных источников поиска.")
        return

    try:
        results_lists = await asyncio.gather(*tasks, return_exceptions=True)
    except Exception as e:
        logger.error(f"Ошибка поиска: {e}", exc_info=True)
        await status_msg.edit_text(f"Ошибка поиска: {e}")
        return

    all_results = []
    for source_name, res in zip(settings.ENABLED_SOURCES, results_lists):
        if isinstance(res, list):
            logger.info(f"{source_name}: найдено {len(res)} вакансий")
            all_results.extend(res)
        else:
            logger.error(f"{source_name} ошибка: {res}")

    if not all_results:
        await status_msg.edit_text(
            "Ничего не найдено.\n"
            "Попробуй упростить запрос: /search маркетолог"
        )
        return

    text = format_results(all_results[: settings.MAX_RESULTS])
    # Telegram лимит 4096 символов
    if len(text) > 4000:
        text = text[:4000] + "\n... (результаты обрезаны)"
    await status_msg.edit_text(text, disable_web_page_preview=True)


@dp.message()
async def fallback(message: Message):
    await message.answer("Используй /search <запрос>, например: /search маркетинг")


async def main():
    async def health(_request):
        return web.Response(text="OK")

    app = web.Application()
    app.router.add_get("/", health)

    runner = web.AppRunner(app)
    await runner.setup()

    port = int(os.getenv("PORT", "10000"))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

    logger.info(f"Health server started on port {port}")
    logger.info("Bot polling started")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
