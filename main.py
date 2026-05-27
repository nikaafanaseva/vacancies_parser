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

if not settings.BOT_TOKEN:
    logger.error("❌ BOT_TOKEN не установлен!")
    sys.exit(1)

if not settings.FIRECRAWL_API_KEY:
    logger.error("❌ FIRECRAWL_API_KEY не установлен!")
    sys.exit(1)

bot = Bot(token=settings.BOT_TOKEN)
dp = Dispatcher()

# Передаём API ключ во все парсеры
parsers = {
    "hh.ru": HHParser(api_key=settings.FIRECRAWL_API_KEY),
    "getmatch.ru": GetMatchParser(api_key=settings.FIRECRAWL_API_KEY),
    "geekjob.ru": GeekJobParser(api_key=settings.FIRECRAWL_API_KEY),
}

@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "👋 <b>Бот поиска вакансий</b>\n\n"
        "Используй: <code>/search &lt;должность&gt;</code>\n\n"
        "Пример: <code>/search Python разработчик</code>",
        parse_mode="HTML"
    )

@dp.message(Command("search"))
async def cmd_search(message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("❌ <b>Формат:</b> <code>/search &lt;запрос&gt;</code>", parse_mode="HTML")
        return
    
    query = safe_format_query(args[1])
    logger.info(f"🔍 Поиск: {query}")
    
    status = await message.answer("🔎 <b>Ищу вакансии...</b>", parse_mode="HTML")
    
    tasks = []
    for source in settings.ENABLED_SOURCES:
        if source in parsers:
            logger.info(f"🚀 Запуск {source}")
            tasks.append(parsers[source].search(query, limit=settings.MAX_RESULTS))
    
    try:
        results_lists = await asyncio.gather(*tasks, return_exceptions=True)
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}", exc_info=True)
        await status.edit_text(f"❌ Ошибка: <code>{e}</code>", parse_mode="HTML")
        return
    
    all_results = []
    for i, res in enumerate(results_lists):
        source = list(settings.ENABLED_SOURCES)[i] if i < len(list(settings.ENABLED_SOURCES)) else "parser"
        if isinstance(res, Exception):
            logger.error(f"❌ {source}: {res}", exc_info=True)
        elif isinstance(res, list):
            logger.info(f"✅ {source}: {len(res)} вакансий")
            all_results.extend(res)
        else:
            logger.warning(f"⚠️ {source}: неожиданный тип {type(res)}")
    
    if not all_results:
        await status.edit_text(
            "😔 <b>Ничего не найдено</b>\n"
            "Попробуйте: <code>/search Python</code>",
            parse_mode="HTML"
        )
        return
    
    formatted = format_results(all_results[:settings.MAX_RESULTS])
    await status.edit_text(formatted, parse_mode="HTML", disable_web_page_preview=True)

@dp.message()
async def echo(message: Message):
    await message.answer("🤔 Используй <code>/search</code>", parse_mode="HTML")

async def main():
    async def handle(r):
        return web.Response(text="✅ Bot is alive")
    
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    
    port = int(os.getenv("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"🌐 Server on port {port}")
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
