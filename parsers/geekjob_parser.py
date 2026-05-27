import aiohttp
import logging
import asyncio
import re
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

logger = logging.getLogger(__name__)


class GeekJobParser:
    """Парсер geekjob.ru"""
    
    def __init__(self):
        self.ua = UserAgent()
        self.base_url = "https://geekjob.ru"

    def _get_headers(self):
        return {
            "User-Agent": self.ua.random,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
            "Referer": "https://geekjob.ru/",
            "Connection": "keep-alive",
        }

    async def search(self, query: str, limit: int = 10) -> list:
        results = []
        params = {"q": query}
        
        try:
            logger.info(f"🔍 GeekJob: поиск '{query}'")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.base_url,
                    params=params,
                    headers=self._get_headers(),
                    timeout=aiohttp.ClientTimeout(total=30),
                    allow_redirects=True
                ) as resp:
                    if resp.status != 200:
                        logger.error(f"❌ GeekJob: HTTP {resp.status}")
                        return []
                    html = await resp.text()
            
            soup = BeautifulSoup(html, 'lxml')
            
            cards = (
                soup.find_all("div", class_=re.compile(r"vacancy|job", re.I)) or
                soup.find_all("article") or
                soup.find_all("li")
            )
            
            logger.info(f"📦 GeekJob: найдено {len(cards)} карточек")
            
            for card in cards[:limit]:
                try:
                    title_tag = card.find("a") or card.find(["h2", "h3"])
                    if not title_tag:
                        continue
                    
                    title = title_tag.get_text(strip=True)
                    link = title_tag.get("href", "") if title_tag.name == "a" else ""
                    
                    if link and not link.startswith("http"):
                        link = f"https://geekjob.ru{link}"
                    
                    company_tag = card.find(class_=re.compile(r"company|employer", re.I))
                    company = company_tag.get_text(strip=True) if company_tag else "Не указано"
                    
                    salary_tag = card.find(class_=re.compile(r"salary|compensation", re.I))
                    salary = salary_tag.get_text(strip=True) if salary_tag else "Не указано"
                    
                    location_tag = card.find(class_=re.compile(r"location|city", re.I))
                    location = location_tag.get_text(strip=True) if location_tag else "Не указано"
                    
                    if title and len(title) > 3:
                        results.append({
                            "title": title,
                            "company": company,
                            "salary": salary,
                            "location": location,
                            "url": link,
                            "source": "geekjob.ru",
                        })
                except Exception as e:
                    logger.warning(f"⚠️ GeekJob: {e}")
                    continue
            
            logger.info(f"✅ GeekJob: {len(results)} вакансий")
            
        except asyncio.TimeoutError:
            logger.error("❌ GeekJob: таймаут")
        except Exception as e:
            logger.error(f"❌ GeekJob: {e}", exc_info=True)
        
        return results
