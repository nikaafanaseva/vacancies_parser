import asyncio
import logging
from playwright.async_api import async_playwright

logger = logging.getLogger(__name__)

class GeekJobParser:
    def __init__(self):
        self.base_url = "https://geekjob.ru"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

    async def search(self, query: str, limit: int = 5) -> list:
        logger.info(f"🔍 GeekJobParser: поиск по запросу '{query}'")
        results = []
        
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    user_agent=self.headers["User-Agent"],
                    viewport={"width": 1920, "height": 1080}
                )
                page = await context.new_page()
                
                url = f"{self.base_url}/?q={query.replace(' ', '+')}"
                logger.info(f"📡 GeekJobParser: запрос к {url}")
                
                await page.goto(url, timeout=30000, wait_until="networkidle")
                await asyncio.sleep(2)
                
                vacancy_cards = await page.query_selector_all(".vacancy, .job-card, article.job")
                
                for card in vacancy_cards[:limit]:
                    try:
                        title_elem = await card.query_selector("h2 a, .title a, h3 a")
                        title = await title_elem.inner_text() if title_elem else "Не указано"
                        
                        link_elem = await card.query_selector("h2 a, .title a, h3 a")
                        link = await link_elem.get_attribute("href") if link_elem else ""
                        
                        if link and not link.startswith("http"):
                            link = f"https://geekjob.ru{link}"
                        
                        company_elem = await card.query_selector(".company, .employer")
                        company = await company_elem.inner_text() if company_elem else "Не указано"
                        
                        salary_elem = await card.query_selector(".salary, .compensation")
                        salary = await salary_elem.inner_text() if salary_elem else "Не указано"
                        
                        location_elem = await card.query_selector(".location, .city")
                        location = await location_elem.inner_text() if location_elem else "Не указано"
                        
                        if title and title != "Не указано":
                            results.append({
                                "title": title.strip(),
                                "company": company.strip(),
                                "salary": salary.strip(),
                                "location": location.strip(),
                                "url": link,
                                "source": "geekjob.ru"
                            })
                            logger.info(f"✅ GeekJobParser: найдено - {title[:50]}...")
                            
                    except Exception as e:
                        logger.warning(f"⚠️ GeekJobParser: ошибка при парсинге: {e}")
                        continue
                
                await browser.close()
                
        except Exception as e:
            logger.error(f"❌ GeekJobParser: критическая ошибка: {e}", exc_info=True)
        
        logger.info(f"📊 GeekJobParser: всего найдено {len(results)} вакансий")
        return results
