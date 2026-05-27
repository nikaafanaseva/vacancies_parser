import re
from typing import List, Dict


def safe_format_query(query: str) -> str:
    # Удаляем только опасные символы, пробелы оставляем
    cleaned = re.sub(r'["\'\\\\]', "", query.strip())
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned[:100]


def format_results(vacancies: List[Dict]) -> str:
    if not vacancies:
        return "❌ Ничего не найдено"

    lines = [f"📋 Найдено: {len(vacancies)}\n"]

    for i, v in enumerate(vacancies, 1):
        lines.append(
            f"{i}. {v.get('title', 'Без названия')}\n"
            f"🏢 {v.get('company', 'Не указано')}\n"
            f"💰 {v.get('salary', 'Не указана')}\n"
            f"📍 {v.get('location', 'Не указано')}\n"
            f"🔗 {v.get('url', '')}\n"
        )

    return "\n".join(lines)
