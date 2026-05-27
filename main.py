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
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

if not settings.BOT_TOKEN:
    logger.error("❌ BOT_TOKEN не установлен!")
    sys.exit(1)

bot = Bot(token=settings.BOT_TOKEN)
dp = Dispatcher()

parsers = {
    "hh.ru": HHParser(),
    "getmatch.ru": GetMatchParser(),
    "geekjob.ru": GeekJobParser(),
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
    logger.info(f"🔍 Поиск от {message.from_user.id}: {message.text}")
    
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer(
            "❌ <b>Неверный формат</b>\n"
            "Используй: <code>/search &lt;должность&gt; &lt;ключевые слова&gt;</code>",
            parse_mode="HTML"
        )
        return

    query = safe_format_query(args[1])
    logger.info(f"📝 Запрос: {query}")
    
    status_msg = await message.answer(f"🔎 <b>Ищу вакансии...</b>", parse_mode="HTML")

    tasks = []
    for source in settings.ENABLED_SOURCES:
        if source in parsers:
            logger.info(f"🚀 Запускаю {source}")
            tasks.append(parsers[source].search(query, limit=settings.MAX_RESULTS))

    try:
        results_lists = await asyncio.gather(*tasks, return_exceptions=True)
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}", exc_info=True)
        await status_msg.edit_text(f"❌ Ошибка: <code>{e}</code>", parse_mode="HTML")
        return

    all_results = []
    for i, res in enumerate(results_lists):
        source_name = list(settings.ENABLED_SOURCES)[i] if i < len(list(settings.ENABLED_SOURCES)) else f"parser_{i}"
        
        if isinstance(res, Exception):
            logger.error(f"❌ {source_name}: {res}", exc_info=True)
        elif isinstance(res, list):
            logger.info(f"✅ {source_name}: {len(res)} вакансий")
            all_results.extend(res)
        else:
            logger.warning(f"⚠️ {source_name}: неожиданный тип {type(res)}")

    logger.info(f"📊 Всего: {len(all_results)} вакансий")

    if not all_results:
        await status_msg.edit_text(
            "😔 <b>Ничего не найдено</b>\n"
            "Попробуйте:\n"
            "• /search Python разработчик\n"
            "• /search Менеджер проектов",
            parse_mode="HTML"
        )
        return

    formatted = format_results(all_results[:settings.MAX_RESULTS])
    await status_msg.edit_text(formatted, parse_mode="HTML", disable_web_page_preview=True)

@dp.message()
async def echo_handler(message: Message):
    await message.answer(
        "🤔 Используй <code>/search</code> для поиска.",
        parse_mode="HTML"
    )

async def main():
    async def handle(request):
        return web.Response(text="✅ Bot is alive")

    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()

    port = int(os.getenv("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logging.info(f"🌐 Server on port {port}")

    logging.info("🤖 Starting bot...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
