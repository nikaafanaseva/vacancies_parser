import re
from typing import List, Dict

def safe_format_query(query: str) -> str:
    cleaned = re.sub(r'[<>\"\'\\]', '', query.strip())
    return cleaned[:100]

def format_results(vacancies: List[Dict]) -> str:
    if not vacancies:
        return "❌ Ничего не найдено"

    lines = [f"📋 <b>Найдено: {len(vacancies)}</b>\n"]

    for i, v in enumerate(vacancies, 1):
        source_emoji = {
            "hh.ru": "🔷",
            "getmatch.ru": "🔶",
            "geekjob.ru": "🟢"
        }.get(v["source"], "🔹")

        lines.append(
            f"{i}. <b>{v['title']}</b>\n"
            f"   {source_emoji} {v['company']}\n"
            f"   💰 {v['salary']}\n"
            f"   📍 {v['location'] or '—'}\n"
            f"   🔗 <a href='{v['url']}'>Открыть вакансию</a>\n"
        )

    return "\n".join(lines)
