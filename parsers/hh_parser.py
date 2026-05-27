import logging
from firecrawl import FirecrawlApp
from bs4 import BeautifulSoup

from parsers.firecrawl_utils import unpack_firecrawl_response

logger = logging.getLogger(__name__)


class HHParser:
    def __init__(self, api_key: str):
        self.base_url = "https://hh.ru/search/vacancy"
        self.app = FirecrawlApp(api_key=api_key)

    async def search(self, query: str, limit: int = 5) -> list:
        logger.info(f"HH: поиск '{query}'")
        results = []

        try:
            url = f"{self.base_url}?text={query.replace(' ', '+')}"
            response = self.app.scrape_url(
                url,
                params={"formats": ["html", "markdown"], "onlyMainContent": False},
            )

            html, _ = unpack_firecrawl_response(response)
            if not html:
                logger.warning("HH: пустой HTML")
                return results

            soup = BeautifulSoup(html, "lxml")

            # Актуальные блоки hh
            cards = soup.select('[data-qa="vacancy-serp__vacancy"]')
            if not cards:
                cards = soup.select("div.vacancy-serp-item")

            for card in cards[:limit]:
                title_tag = card.select_one('[data-qa="serp-item__title"]') or card.select_one("a.bloko-link")
                if not title_tag:
                    continue

                title = title_tag.get_text(strip=True)
                link = title_tag.get("href", "")
                if link and not link.startswith("http"):
                    link = f"https://hh.ru{link}"

                company_tag = (
                    card.select_one('[data-qa="vacancy-serp__vacancy-employer-text"]')
                    or card.select_one('[data-qa="vacancy-serp__vacancy-employer"]')
                )
                company = company_tag.get_text(strip=True) if company_tag else "Не указано"

                salary_tag = card.select_one('[data-qa*="vacancy-compensation"]')
                salary = salary_tag.get_text(strip=True) if salary_tag else "Не указано"

                city_tag = card.select_one('[data-qa="vacancy-serp__vacancy-address"]')
                city = city_tag.get_text(strip=True) if city_tag else "Не указано"

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

        except Exception as e:
            logger.error(f"HHParser error: {e}", exc_info=True)

        logger.info(f"HH: найдено {len(results)}")
        return results
