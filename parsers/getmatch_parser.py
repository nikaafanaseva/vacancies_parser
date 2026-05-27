import logging
import re
from firecrawl import FirecrawlApp
from bs4 import BeautifulSoup

from parsers.firecrawl_utils import unpack_firecrawl_response

logger = logging.getLogger(__name__)


class GetMatchParser:
    def __init__(self, api_key: str):
        self.base_url = "https://getmatch.ru/vacancies"
        self.app = FirecrawlApp(api_key=api_key)

    async def search(self, query: str, limit: int = 5) -> list:
        logger.info(f"GetMatch: поиск '{query}'")
        results = []

        try:
            url = f"{self.base_url}?search={query.replace(' ', '+')}"
            response = self.app.scrape_url(
                url,
                params={"formats": ["html", "markdown"], "onlyMainContent": False},
            )

            html, markdown = unpack_firecrawl_response(response)

            # 1) Пробуем HTML
            if html:
                soup = BeautifulSoup(html, "lxml")
                cards = soup.find_all(["article", "div", "li"], class_=re.compile(r"vacancy|job", re.I))

                for card in cards[: limit * 3]:
                    title_tag = card.find(["h2", "h3", "a"])
                    if not title_tag:
                        continue

                    title = title_tag.get_text(strip=True)
                    if len(title) < 4:
                        continue

                    link_tag = card.find("a")
                    link = link_tag.get("href", "") if link_tag else ""
                    if link and not link.startswith("http"):
                        link = f"https://getmatch.ru{link}"

                    company_tag = card.find(class_=re.compile(r"company|employer", re.I))
                    salary_tag = card.find(class_=re.compile(r"salary|compensation", re.I))
                    location_tag = card.find(class_=re.compile(r"location|city", re.I))

                    results.append(
                        {
                            "title": title,
                            "company": company_tag.get_text(strip=True) if company_tag else "Не указано",
                            "salary": salary_tag.get_text(strip=True) if salary_tag else "Не указано",
                            "location": location_tag.get_text(strip=True) if location_tag else "Не указано",
                            "url": link,
                            "source": "getmatch.ru",
                        }
                    )
                    if len(results) >= limit:
                        return results

            # 2) Fallback: markdown-ссылки
            if markdown and len(results) < limit:
                links = re.findall(r"\[([^\]]+)\]\((https?://getmatch\.ru[^\)]+)\)", markdown)
                for title, link in links:
                    title = title.strip()
                    if len(title) < 4:
                        continue
                    results.append(
                        {
                            "title": title,
                            "company": "Не указано",
                            "salary": "Не указано",
                            "location": "Не указано",
                            "url": link,
                            "source": "getmatch.ru",
                        }
                    )
                    if len(results) >= limit:
                        break

        except Exception as e:
            logger.error(f"GetMatch error: {e}", exc_info=True)

        logger.info(f"GetMatch: найдено {len(results)}")
        return results
