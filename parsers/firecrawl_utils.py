from typing import Any, Dict, Tuple


def unpack_firecrawl_response(response: Any) -> Tuple[str, str]:
    """
    Firecrawl может вернуть:
    1) {"success": true, "data": {...}}
    2) сразу {...}
    """
    if not isinstance(response, dict):
        return "", ""

    data: Dict = response.get("data", response)
    if not isinstance(data, dict):
        return "", ""

    html = data.get("html") or data.get("rawHtml") or ""
    markdown = data.get("markdown") or ""
    return html, markdown
