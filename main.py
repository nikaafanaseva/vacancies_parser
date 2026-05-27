import logging
import sys
import os
import asyncio
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message

from config import settings
from parsers.habr_parser import HabrParser
from parsers.getmatch_parser import GetMatchParser
from parsers.rabota_parser import RabotaParser
from utils import format_results, safe_format_query

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

if not settings.BOT_TOKEN:
    logger.error("BOT_TOKEN not set")
    sys.exit(1)

logger.info("Token loaded OK")

bot = Bot(token=settings.BOT_TOKEN)
dp = Dispatcher()

parsers = {
    "getmatch.ru": GetMatchParser(),
    "Хабр Карьера": HabrParser(),
    "rabota.ru": RabotaParser(),
}


@dp.message(Command("start"))
async def cmd_start(message: Message):
    text = (
        "👋 <b>Бот поиска вакансий</b>\n\n"
        "Используй: <code>/search &lt;должность&gt;</code>\n\n"
        "<b>Примеры:</b>\n"
        "<code>/search маркетолог</code>\n"
        "<code>/search Python</code>\n\n"
        "<b>Источники:</b>\n"
        "- Хабр Карьера\n"
        "- getmatch.ru\n"
        "- rabota.ru"
    )
    await message.answer(text, parse_mode="HTML")


@dp.message(Command("search"))
async def cmd_search(message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer(
            "Формат: <code>/search маркетолог</code>",
            parse_mode="HTML"
        )
        return

    query = safe_format_query(args[1])
    logger.info("Search: " + query)

    status_msg = await message.answer(
        "Ищу вакансии: <code>" + query + "</code>",
        parse_mode="HTML"
    )

    tasks = []
    sources = []
    for source in settings.ENABLED_SOURCES:
        if source in parsers:
            tasks.append(parsers[source].search(query, limit=settings.MAX_RESULTS))
            sources.append(source)

    if not tasks:
        await status_msg.edit_text("Нет источников", parse_mode="HTML")
        return

    results_lists = await asyncio.gather(*tasks, return_exceptions=True)

    all_results = []
    for i, res in enumerate(results_lists):
        source = sources[i] if i < len(sources) else "?"
        if isinstance(res, Exception):
            logger.error(source + " error: " + str(res))
        elif isinstance(res, list):
            logger.info(source + " found: " + str(len(res)))
            all_results.extend(res)

    if not all_results:
        await status_msg.edit_text(
            "Ничего не найдено. Попробуй другой запрос.",
            parse_mode="HTML"
        )
        return

    formatted = format_results(all_results[:settings.MAX_RESULTS])
    await status_msg.edit_text(
        formatted,
        parse_mode="HTML",
        disable_web_page_preview=True
    )


@dp.message()
async def echo_handler(message: Message):
    await message.answer(
        "Используй <code>/search маркетолог</code>",
        parse_mode="HTML"
    )


async def main():
    async def handle(request):
        return web.Response(text="OK")

    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()

    port = int(os.getenv("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info("Server on port " + str(port))
    logger.info("Starting bot...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
