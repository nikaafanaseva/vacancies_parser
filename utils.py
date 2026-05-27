import re
import html


def safe_format_query(query: str) -> str:
    """Очистка запроса"""
    query = query.strip()
    query = re.sub(r'[<>]', '', query)
    return query


def format_results(results: list) -> str:
    """Форматирование результатов"""
    if not results:
        return "😔 Ничего не найдено"
    
    output = [f"🎯 <b>Найдено вакансий: {len(results)}</b>\n"]
    
    for i, v in enumerate(results, 1):
        title = html.escape(v.get("title", "Вакансия"))
        company = html.escape(v.get("company", "Не указано"))
        salary = html.escape(v.get("salary", "Не указано"))
        location = html.escape(v.get("location", "Не указано"))
        source = html.escape(v.get("source", ""))
        url = v.get("url", "")
        
        text = f"{i}. <b>{title}</b>\n"
        text += f"   🏢 {company}\n"
        if salary != "Не указано":
            text += f"   💰 {salary}\n"
        if location != "Не указано":
            text += f"   📍 {location}\n"
        text += f"   📡 {source}"
        if url:
            text += f"\n   🔗 <a href='{url}'>Открыть</a>"
        
        output.append(text)
    
    return "\n\n".join(output)
