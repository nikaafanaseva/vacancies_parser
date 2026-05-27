import logging
import sys
import os
import asyncio
from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
from config import settings
from parsers.hh_parser import HHParser
from parsers.getmatch_parser import GetMatchParser
from parsers.geekjob_parser import GeekJobParser
from utils import format_results, safe_format_query

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# 🔥 ПРОВЕРКА ТОКЕНА (пункт 3)
if not settings.BOT_TOKEN:
    logger.error("❌ BOT_TOKEN не установлен! Проверьте переменные окружения на Render")
    sys.exit(1)
else:
    logger.info(f"✅ Token loaded: {settings.BOT_TOKEN[:10]}...")

# Инициализация бота и диспетчера
bot = Bot(token=settings.BOT_TOKEN)
dp = Dispatcher()

# Инициализация парсеров
parsers = {
    "hh.ru": HHParser(),
    "getmatch.ru": GetMatchParser(),
    "geekjob.ru": GeekJobParser(),
}

# 🔥 ИСПРАВЛЕНО: CommandStart() → Command("start") (пункт 2)
@dp.message(Command("start"))
async def cmd_start(message: Message):
    logger.info(f"📩 Получена команда /start от пользователя {message.from_user.id}")
    await message.answer(
        "👋 **Бот поиска вакансий**\n\n"
        "Используй команду:\n"
        "`/search <должность> <ключевые слова>`\n\n"
        "Примеры:\n"
        "`/search Python разработчик удалённо`\n"
        "`/search Менеджер проектов Москва`\n\n"
        "Источники: hh.ru, getmatch.ru, geekjob.ru",
        parse_mode="HTML"
    )

@dp.message(Command("search"))
async def cmd_search(message: Message):
    logger.info(f"🔍 Поиск от {message.from_user.id}: {message.text}")
    
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer(
            "❌ **Неверный формат**\n"
            "Используй: `/search <должность> <ключевые слова>`\n"
            "Пример: `/search Java разработчик СПб`",
            parse_mode="HTML"
        )
        return

    query = safe_format_query(args[1])
    status_msg = await message.answer(f"🔎 **Поиск по запросу:** `{query}`...", parse_mode="HTML")

    # Собираем задачи только для включённых источников
    tasks = [
        parsers[source].search(query, limit=settings.MAX_RESULTS)
        for source in settings.ENABLED_SOURCES
        if source in parsers
    ]

    try:
        results_lists = await asyncio.gather(*tasks, return_exceptions=True)
    except Exception as e:
        logger.error(f"❌ Ошибка при поиске: {e}")
        await status_msg.edit_text(f"❌ Ошибка при поиске: `{e}`", parse_mode="HTML")
        return

    # Объединяем результаты
    all_results = []
    for res in results_lists:
        if isinstance(res, list):
            all_results.extend(res)
        else:
            logger.error(f"Ошибка парсера: {res}")

    if not all_results:
        await status_msg.edit_text(
            "😔 **Ничего не найдено**\n"
            "Попробуй:\n"
            "• Изменить формулировку\n"
            "• Убрать редкие ключевые слова\n"
            "• Проверить позже",
            parse_mode="HTML"
        )
        return

    # Отправляем отформатированный список
    formatted = format_results(all_results[:settings.MAX_RESULTS])
    await status_msg.edit_text(formatted, parse_mode="HTML", disable_web_page_preview=True)

@dp.message()
async def echo_handler(message: Message):
    await message.answer(
        "🤔 Используй команду `/search` для поиска вакансий.\n"
        "Например: `/search React разработчик удалённо`",
        parse_mode="HTML"
    )

async def main():
    # 1️⃣ Лёгкий HTTP-сервер для Render (чтобы бесплатный тариф не засыпал)
    async def handle(request):
        return web.Response(text="✅ Bot is alive and polling.")

    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()

    port = int(os.getenv("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logging.info(f"🌐 Health server running on port {port}")

    # 2️⃣ Запуск Telegram бота
    logging.info("🤖 Starting bot polling...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
