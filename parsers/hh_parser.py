import logging
import re
from bs4 import BeautifulSoup
from firecrawl import FirecrawlApp

from parsers.firecrawl_utils import unpack_firecrawl_response

logger = logging.getLogger(__name__)


class HHParser:
    def __init__(self, api_key: str):
        self.base_url = "https://hh.ru/search/vacancy"
        self.app = FirecrawlApp(api_key=api_key)

    async def search(self, query: str, limit: int = 5) -> list:
        results = []
        try:
            url = f"{self.base_url}?text={query.replace(' ', '+')}"
            logger.info(f"HH URL: {url}")

            # ВАЖНО: в новой версии firecrawl-py НЕ используем params=
            response = self.app.scrape_url(url, formats=["markdown", "html"])
            html, markdown = unpack_firecrawl_response(response)

            # 1) Пытаемся вытащить из HTML
            if html:
                soup = BeautifulSoup(html, "lxml")
                cards = soup.select('[data-qa="vacancy-serp__vacancy"]')
                if not cards:
                    cards = soup.select("div.vacancy-serp-item")

                for card in cards:
                    if len(results) >= limit:
                        break

                    title_tag = card.select_one('[data-qa="serp-item__title"]') or card.select_one("a")
                    if not title_tag:
                        continue

                    title = title_tag.get_text(" ", strip=True)
                    if len(title) < 4:
                        continue

                    link = title_tag.get("href", "")
                    if link and not link.startswith("http"):
                        link = f"https://hh.ru{link}"

                    company_tag = card.select_one('[data-qa="vacancy-serp__vacancy-employer-text"]')
                    company = company_tag.get_text(" ", strip=True) if company_tag else "Не указано"

                    salary_tag = card.select_one('[data-qa*="vacancy-compensation"]')
                    salary = salary_tag.get_text(" ", strip=True) if salary_tag else "Не указана"

                    city_tag = card.select_one('[data-qa="vacancy-serp__vacancy-address"]')
                    city = city_tag.get_text(" ", strip=True) if city_tag else "Не указано"

                    results.append(
                        {
                            "title": title,
                            "company": company,
                            "salary": salary,
                            "location": city,
                            "url": link,
                            "source": "hh.ru",
                        }
                    )

            # 2) Fallback: парсим markdown-ссылки
            if len(results) < limit and markdown:
                links = re.findall(r"\[([^\]]+)\]\((https?://hh\.ru/vacancy/[^\)]+)\)", markdown)
                for title, link in links:
                    if len(results) >= limit:
                        break
                    title = title.strip()
                    if len(title) < 4:
                        continue
                    results.append(
                        {
                            "title": title,
                            "company": "Не указано",
                            "salary": "Не указана",
                            "location": "Не указано",
                            "url": link,
                            "source": "hh.ru",
                        }
                    )

        except Exception as e:
            logger.error(f"HHParser error: {e}", exc_info=True)

        logger.info(f"HH: найдено {len(results)}")
        return results
