import logging
import sys
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, CommandStart
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

bot = Bot(token=settings.BOT_TOKEN)
dp = Dispatcher()

parsers = {
    "hh.ru": HHParser(),
    "getmatch.ru": GetMatchParser(),
    "geekjob.ru": GeekJobParser(),
}

@dp.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        "👋 <b>Бот поиска вакансий</b>\n\n"
        "Используй команду:\n"
        "<code>/search <должность> <ключевые слова></code>\n\n"
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
            "Используй: <code>/search <должность> <ключевые слова></code>\n"
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
        await status_msg.edit_text(f"❌ Ошибка при поиске: <code>{e}</code>", parse_mode="HTML")
        return

    all_results = []
    for res in results_lists:
        if isinstance(res, list):
            all_results.extend(res)
        else:
            logger.error(f"Ошибка парсера: {res}")

    if not all_results:
        await status_msg.edit_text("😔 <b>Ничего не найдено</b>\nПопробуй:\n• Изменить формулировку\n• Убрать редкие ключевые слова\n• Проверить позже", parse_mode="HTML")
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
    logger.info("🚀 Vacancy bot starting...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
