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

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Проверка токена
if not settings.BOT_TOKEN:
    logger.error("❌ BOT_TOKEN не установлен! Проверьте переменные окружения на Render.")
    sys.exit(1)
else:
    logger.info(f"✅ Token loaded: {settings.BOT_TOKEN[:10]}...")

# Инициализация бота и диспетчера
bot = Bot(token=settings.BOT_TOKEN)
dp = Dispatcher()

# Инициализация парсеров
parsers = {
    "Хабр Карьера": HabrParser(),
    "getmatch.ru": GetMatchParser(),
    "rabota.ru": RabotaParser(),
}


@dp.message(Command("start"))
async def cmd_start(message: Message):
    logger.info(f"📩 /start от пользователя {message.from_user.id}")
    await message.answer(
        "👋 <b>Бот поиска вакансий</b>\n\n"
        "Используй команду:\n"
        "<code>/search &lt;должность&gt;</code>\n\n"
        "<b>Примеры:</b>\n"
        "<code>/search маркетолог</code>\n"
        "<code>/search Python разработчик</code>\n"
        "<code>/search SMM менеджер</code>\n\n"
        "<b>📡 Источники:</b>\n"
        "• Хабр Карьера\n"
        "• getmatch.ru\n"
        "• rabota.ru",
        parse_mode="HTML"
    )


@dp.message(Command("search"))
async def cmd_search(message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer(
            "❌ <b>Неверный формат</b>\n"
            "Используй: <code>/search &lt;должность&gt;</code>\n"
            "Пример: <code>/search маркетолог</code>",
            parse_mode="HTML"
        )
        return

    query = safe_format_query(args[1])
    logger.info(f"🔍 Поиск от {message.from_user.id}: '{query}'")
    
    status_msg = await message.answer(
        f"🔎 <b>Ищу вакансии:</b> <code>{query}</code>\n"
        f"⏳ Проверяю 3 источника, это займёт до 30 секунд...",
        parse_mode="HTML"
    )

    # Формируем задачи для всех активных источников
    tasks = []
    active_sources = []
    for source in settings.ENABLED_SOURCES:
        if source in parsers:
            tasks.append(parsers[source].search(query, limit=settings.MAX_RESULTS))
            active_sources.append(source)
    
    if not tasks:
        await status_msg.edit_text(
            "❌ <b>Ошибка конфигурации</b>\n"
            "Нет активных источников для поиска.",
            parse_mode="HTML"
        )
        return

    # Запускаем все парсеры параллельно
    try:
        results_lists = await asyncio.gather(*tasks, return_exceptions=True)
    except Exception as e:
        logger.error(f"❌ Критическая ошибка при поиске: {e}", exc_info=True)
        await status_msg.edit_text(
            f"❌ <b>Ошибка при поиске:</b>\n<code>{e}</code>",
            parse_mode="HTML"
        )
        return

    # Собираем результаты
    all_results = []
    for i, res in enumerate(results_lists):
        source = active_sources[i] if i < len(active_sources) else "?"
        if isinstance(res, Exception):
            logger.error(f"❌ {source}: {res}", exc_info=True)
        elif isinstance(res, list):
            logger.info(f"✅ {source}: найдено {len(res)} вакансий")
            all_results.extend(res)
        else:
            logger.warning(f"⚠️ {source}: неожиданный тип результата {type(res)}")

    # Если ничего не найдено
    if not all_results:
        await status_msg.edit_text(
            "😔 <b>Ничего не найдено</b>\n\n"
            "Попробуйте:\n"
            "• Изменить формулировку\n"
            "• Использовать более общее слово\n"
            "• Проверить позже",
            parse_mode="HTML"
        )
        return

    # Форматируем и отправляем результаты
    formatted = format_results(all_results[:settings.MAX_RESULTS])
    await status_msg.edit_text(
        formatted,
        parse_mode="HTML",
        disable_web_page_preview=True
    )


@dp.message()
async def echo_handler(message: Message):
    await message.answer(
        "🤔 Используй команду <code>/search</code> для поиска вакансий.\n"
        "Например: <code>/search маркетолог</code>",
        parse_mode="HTML"
    )


async def main():
    # HTTP-сервер для Render (health-check)
    async def handle(request):
        return web.Response(text="✅ Bot is alive
