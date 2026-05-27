import logging
import re
from bs4 import BeautifulSoup
from firecrawl import FirecrawlApp

from parsers.firecrawl_utils import unpack_firecrawl_response

logger = logging.getLogger(__name__)


class GeekJobParser:
    def __init__(self, api_key: str):
        self.base_url = "https://geekjob.ru/vacancies"
        self.app = FirecrawlApp(api_key=api_key)

    async def search(self, query: str, limit: int = 5) -> list:
        results = []
        try:
            url = f"{self.base_url}?q={query.replace(' ', '+')}"
            logger.info(f"GeekJob URL: {url}")

            response = self.app.scrape_url(url, formats=["markdown", "html"])
            html, markdown = unpack_firecrawl_response(response)

            # 1) HTML
            if html:
                soup = BeautifulSoup(html, "lxml")
                cards = soup.find_all(["article", "div", "li"], class_=re.compile(r"vacancy|job", re.I))

                for card in cards:
                    if len(results) >= limit:
                        break

                    title_tag = card.find(["h2", "h3", "a"])
                    if not title_tag:
                        continue

                    title = title_tag.get_text(" ", strip=True)
                    if len(title) < 4:
                        continue

                    link_tag = card.find("a")
                    link = link_tag.get("href", "") if link_tag else ""
                    if link and link.startswith("/"):
                        link = f"https://geekjob.ru{link}"

                    company_tag = card.find(class_=re.compile(r"company|employer", re.I))
                    salary_tag = card.find(class_=re.compile(r"salary|compensation", re.I))
                    location_tag = card.find(class_=re.compile(r"location|city", re.I))

                    results.append(
                        {
                            "title": title,
                            "company": company_tag.get_text(" ", strip=True) if company_tag else "Не указано",
                            "salary": salary_tag.get_text(" ", strip=True) if salary_tag else "Не указана",
                            "location": location_tag.get_text(" ", strip=True) if location_tag else "Не указано",
                            "url": link,
                            "source": "geekjob.ru",
                        }
                    )

            # 2) Fallback markdown
            if len(results) < limit and markdown:
                links = re.findall(r"\[([^\]]+)\]\((https?://geekjob\.ru[^\)]+)\)", markdown)
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
                            "source": "geekjob.ru",
                        }
                    )

        except Exception as e:
            logger.error(f"GeekJobParser error: {e}", exc_info=True)

        logger.info(f"GeekJob: найдено {len(results)}")
        return results
