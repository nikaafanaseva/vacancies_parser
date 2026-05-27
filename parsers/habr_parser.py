import aiohttp
import logging
import re
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class HabrParser:
    """Парсер Хабр Карьеры (career.habr.com)"""
    
    def __init__(self):
        self.base_url = "https://career.habr.com/vacancies"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
        }

    async def search(self, query: str, limit: int = 10) -> list:
        results = []
        params = {"q": query}
        
        try:
            logger.info(f"🔍 Хабр Карьера: поиск '{query}'")
            timeout = aiohttp.ClientTimeout(total=45)
            
            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url, params=params, headers=self.headers, timeout=timeout) as resp:
                    logger.info(f"📡 Хабр: статус {resp.status}")
                    if resp.status != 200:
                        return []
                    html = await resp.text()
            
            soup = BeautifulSoup(html, 'lxml')
            cards = soup.find_all("div", class_="vacancy-card")
            
            logger.info(f"📦 Хабр: найдено {len(cards)} карточек")
            
            for card in cards[:limit]:
                try:
                    title_tag = card.find("a", class_="vacancy-card__title-link")
                    if not title_tag:
                        continue
                    
                    title = title_tag.get_text(strip=True)
                    link = title_tag.get("href", "")
                    if link and not link.startswith("http"):
                        link = f"https://career.habr.com{link}"
                    
                    company_tag = card.find("a", class_="vacancy-card__company-link")
                    company = company_tag.get_text(strip=True) if company_tag else "Не указано"
                    
                    salary_tag = card.find("div", class_="vacancy-card__salary")
                    salary = salary_tag.get_text(strip=True) if salary_tag else "Не указано"
                    
                    city_tag = card.find("span", class_="vacancy-card__city")
                    location = city_tag.get_text(strip=True) if city_tag else "Не указано"
                    
                    results.append({
                        "title": title,
                        "company": company,
                        "salary": salary,
                        "location": location,
                        "url": link,
                        "source": "Хабр Карьера"
                    })
                except Exception as e:
                    logger.warning(f"⚠️ Хабр: {e}")
                    continue
            
            logger.info(f"✅ Хабр: {len(results)} вакансий")
            return results
            
        except Exception as e:
            logger.error(f"❌ Хабр: {e}", exc_info=True)
            return []
