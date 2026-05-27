import logging
import sys
import os
import asyncio
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
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Проверка токенов
if not settings.BOT_TOKEN:
    logger.error("❌ BOT_TOKEN не установлен! Проверьте переменные окружения на Render.")
    sys.exit(1)

if not settings.FIRECRAWL_API_KEY:
    logger.error("❌ FIRECRAWL_API_KEY не установлен! Проверьте переменные окружения на Render.")
    sys.exit(1)

bot = Bot(token=settings.BOT_TOKEN)
dp = Dispatcher()

# Передаём api_key в парсеры (это было главной ошибкой!)
parsers = {
    "hh.ru": HHParser(api_key=settings.FIRECRAWL_API_KEY),
    "getmatch.ru": GetMatchParser(api_key=settings.FIRECRAWL_API_KEY),
    "geekjob.ru": GeekJobParser(api_key=settings.FIRECRAWL_API_KEY),
}

@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "👋 <b>Бот поиска вакансий</b>\n\n"
        "Используй команду:\n"
        "<code>/search &lt;должность&gt; &lt;ключевые слова&gt;</code>\n\n"
        "Примеры:\n"
        "<code>/search Python разработчик удалённо</code>\n"
        "<code>/search Менеджер проектов Москва</code>\n\n"
        "Источники: hh.ru, getmatch.ru, geekjob.ru",
        parse_mode="HTML"
    )

@dp.message(Command("search"))
async def cmd_search(message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer(
            "❌ <b>Неверный формат</b>\n"
            "Используй: <code>/search &lt;должность&gt; &lt;ключевые слова&gt;</code>\n"
            "Пример: <code>/search Java разработчик СПб</code>",
            parse_mode="HTML"
        )
        return

    query = safe_format_query(args[1])
    status_msg = await message.answer(f"🔎 <b>Поиск по запросу:</b> <code>{query}</code>...", parse_mode="HTML")

    tasks = [
        parsers[source].search(query, limit=settings.MAX_RESULTS)
        for source in settings.ENABLED_SOURCES
        if source in parsers
    ]

    try:
        results_lists = await asyncio.gather(*tasks, return_exceptions=True)
    except Exception as e:
        logger.error(f"Ошибка при поиске: {e}")
        await status_msg.edit_text(f"❌ Ошибка при поиске: <code>{e}</code>", parse_mode="HTML")
        return

    all_results = []
    for res in results_lists:
        if isinstance(res, list):
            all_results.extend(res)
        else:
            logger.error(f"Ошибка парсера: {res}")

    if not all_results:
        await status_msg.edit_text(
            "😔 <b>Ничего не найдено</b>\n"
            "Попробуй:\n"
            "• Изменить формулировку\n"
            "• Убрать редкие ключевые слова\n"
            "• Проверить позже",
            parse_mode="HTML"
        )
        return

    formatted = format_results(all_results[:settings.MAX_RESULTS])
    await status_msg.edit_text(formatted, parse_mode="HTML", disable_web_page_preview=True)

@dp.message()
async def echo_handler(message: Message):
    await message.answer(
        "🤔 Используй команду <code>/search</code> для поиска вакансий.\n"
        "Например: <code>/search React разработчик удалённо</code>",
        parse_mode="HTML"
    )

async def main():
    async def handle(request):
        return web.Response(text="✅ Bot is alive and polling.")

    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()

    port = int(os.getenv("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"🌐 Health server running on port {port}")

    logger.info("🤖 Starting bot polling...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
