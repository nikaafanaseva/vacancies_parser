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

bot = Bot(token=settings.BOT_TOKEN)
dp = Dispatcher()

# Инициализация парсеров
parsers = {
    "hh.ru": HHParser(),
    "getmatch.ru": GetMatchParser(),
    "geekjob.ru": GeekJobParser(),
}


@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "👋 <b>Бот поиска вакансий</b>\n\n"
        "Используй: <code>/search &lt;должность&gt;</code>\n\n"
        "<b>Примеры:</b>\n"
        "<code>/search маркетолог</code>\n"
        "<code>/search Python разработчик</code>\n"
        "<code>/search SMM менеджер</code>\n\n"
        "<b>📡 Источники:</b>\n"
        "• hh.ru (официальное API)\n"
        "• getmatch.ru\n"
        "• geekjob.ru",
        parse_mode="HTML"
    )


@dp.message(Command("search"))
async def cmd_search(message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer(
            "❌ Формат: <code>/search &lt;запрос&gt;</code>",
            parse_mode="HTML"
        )
        return

    query = safe_format_query(args[1])
    logger.info(f"🔍 Поиск от {message.from_user.id}: '{query}'")
    
    status_msg = await message.answer(
        f"🔎 <b>Ищу:</b> <code>{query}</code>\n⏳ Секундочку...",
        parse_mode="HTML"
    )

    # Запускаем все парсеры параллельно
    tasks = []
    for source in settings.ENABLED_SOURCES:
        if source in parsers:
            tasks.append(parsers[source].search(query, limit=settings.MAX_RESULTS))
    
    try:
        results_lists = await asyncio.gather(*tasks, return_exceptions=True)
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}", exc_info=True)
        await status_msg.edit_text(f"❌ Ошибка: <code>{e}</code>", parse_mode="HTML")
        return

    # Собираем результаты
    all_results = []
    for i, res in enumerate(results_lists):
        source = settings.ENABLED_SOURCES[i] if i < len(settings.ENABLED_SOURCES) else "?"
        if isinstance(res, Exception):
            logger.error(f"❌ {source}: {res}")
        elif isinstance(res, list):
            logger.info(f"✅ {source}: {len(res)}")
            all_results.extend(res)
        else:
            logger.warning(f"⚠️ {source}: неожиданный тип {type(res)}")

    if not all_results:
        await status_msg.edit_text(
            "😔 <b>Ничего не найдено</b>\n"
            "Попробуйте другой запрос.",
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
        "🤔 Используй <code>/search маркетолог</code>",
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
    logger.info(f"🌐 Server on port {port}")

    logger.info("🤖 Starting bot...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
