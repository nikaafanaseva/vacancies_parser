import asyncio
import logging
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class HHParser:
    def __init__(self):
        self.base_url = "https://hh.ru/search/vacancy"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    async def search(self, query: str, limit: int = 5) -> list:
        logger.info(f"🔍 HHParser: поиск по запросу '{query}'")
        results = []
        
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    user_agent=self.headers["User-Agent"],
                    viewport={"width": 1920, "height": 1080}
                )
                page = await context.new_page()
                
                params = {
                    "text": query,
                    "clusters": "true"
                }
                
                url = f"{self.base_url}?text={query.replace(' ', '+')}"
                logger.info(f"📡 HHParser: запрос к {url}")
                
                await page.goto(url, timeout=30000, wait_until="networkidle")
                await asyncio.sleep(2)  # Ждём загрузки JS
                
                # Парсим вакансии
                vacancy_cards = page.locator("div.vacancy-serp-item").all()
                
                for i, card in enumerate(vacancy_cards[:limit]):
                    try:
                        title_elem = await card.query_selector("a.bloko-link")
                        title = await title_elem.inner_text() if title_elem else "Не указано"
                        
                        link_elem = await card.query_selector("a.bloko-link")
                        link = await link_elem.get_attribute("href") if link_elem else ""
                        
                        if link and not link.startswith("http"):
                            link = f"https://hh.ru{link}"
                        
                        company_elem = await card.query_selector("[data-qa='vacancy-serp__vacancy-employer']")
                        company = await company_elem.inner_text() if company_elem else "Не указано"
                        
                        salary_elem = await card.query_selector("[data-qa='vacancy-serp__vacancy-compensation']")
                        salary = await salary_elem.inner_text() if salary_elem else "Не указано"
                        
                        city_elem = await card.query_selector("[data-qa='vacancy-serp__vacancy-address']")
                        city = await city_elem.inner_text() if city_elem else "Не указано"
                        
                        results.append({
                            "title": title.strip(),
                            "company": company.strip(),
                            "salary": salary.strip(),
                            "location": city.strip(),
                            "url": link,
                            "source": "hh.ru"
                        })
                        
                        logger.info(f"✅ HHParser: найдено - {title[:50]}...")
                        
                    except Exception as e:
                        logger.warning(f"⚠️ HHParser: ошибка при парсинге карточки: {e}")
                        continue
                
                await browser.close()
                
        except Exception as e:
            logger.error(f"❌ HHParser: критическая ошибка: {e}", exc_info=True)
        
        logger.info(f"📊 HHParser: всего найдено {len(results)} вакансий")
        return results
