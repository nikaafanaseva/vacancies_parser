from typing import Dict, Tuple


def unpack_firecrawl_response(response: Dict) -> Tuple[str, str]:
    """
    Нормализует ответ firecrawl-py:
    - иногда SDK возвращает payload с ключом data
    - иногда сразу data-объект
    """
    if not isinstance(response, dict):
        return "", ""

    data = response.get("data", response)
    if not isinstance(data, dict):
        return "", ""

    html = data.get("html") or data.get("rawHtml") or ""
    markdown = data.get("markdown") or ""

    return html, markdown
