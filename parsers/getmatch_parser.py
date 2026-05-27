import aiohttp
import logging
import asyncio
import re
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

logger = logging.getLogger(__name__)


class GetMatchParser:
    """Парсер getmatch.ru с обходом блокировок"""
    
    def __init__(self):
        self.ua = UserAgent()
        self.base_url = "https://getmatch.ru/vacancies"

    def _get_headers(self):
        return {
            "User-Agent": self.ua.random,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Referer": "https://getmatch.ru/",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Cache-Control": "max-age=0",
        }

    async def search(self, query: str, limit: int = 10) -> list:
        results = []
        params = {"search": query}
        
        try:
            logger.info(f"🔍 GetMatch: поиск '{query}'")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.base_url,
                    params=params,
                    headers=self._get_headers(),
                    timeout=aiohttp.ClientTimeout(total=30),
                    allow_redirects=True
                ) as resp:
                    if resp.status != 200:
                        logger.error(f"❌ GetMatch: HTTP {resp.status}")
                        return []
                    html = await resp.text()
            
            soup = BeautifulSoup(html, 'lxml')
            
            # Ищем карточки вакансий разными способами
            cards = (
                soup.find_all("div", class_=re.compile(r"vacancy", re.I)) or
                soup.find_all("article") or
                soup.find_all("li", class_=re.compile(r"vacancy|job", re.I))
            )
            
            logger.info(f"📦 GetMatch: найдено {len(cards)} карточек")
            
            for card in cards[:limit]:
                try:
                    # Заголовок
                    title_tag = (
                        card.find(["h2", "h3", "h4"], class_=re.compile(r"title", re.I)) or
                        card.find("a", class_=re.compile(r"title", re.I)) or
                        card.find(["h2", "h3"])
                    )
                    if not title_tag:
                        continue
                    
                    title = title_tag.get_text(strip=True)
                    
                    # Ссылка
                    link_tag = card.find("a", href=True)
                    link = link_tag["href"] if link_tag else ""
                    if link and not link.startswith("http"):
                        link = f"https://getmatch.ru{link}"
                    
                    # Компания
                    company_tag = card.find(class_=re.compile(r"company|employer", re.I))
                    company = company_tag.get_text(strip=True) if company_tag else "Не указано"
                    
                    # Зарплата
                    salary_tag = card.find(class_=re.compile(r"salary|compensation|price", re.I))
                    salary = salary_tag.get_text(strip=True) if salary_tag else "Не указано"
                    
                    # Город
                    location_tag = card.find(class_=re.compile(r"location|city|address", re.I))
                    location = location_tag.get_text(strip=True) if location_tag else "Не указано"
                    
                    if title and len(title) > 3:
                        results.append({
                            "title": title,
                            "company": company,
                            "salary": salary,
                            "location": location,
                            "url": link,
                            "source": "getmatch.ru",
                        })
                except Exception as e:
                    logger.warning(f"⚠️ GetMatch: {e}")
                    continue
            
            logger.info(f"✅ GetMatch: {len(results)} вакансий")
            
        except asyncio.TimeoutError:
            logger.error("❌ GetMatch: таймаут")
        except Exception as e:
            logger.error(f"❌ GetMatch: {e}", exc_info=True)
        
        return results
