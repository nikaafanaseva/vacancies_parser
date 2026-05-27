import aiohttp
import logging
import re
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

logger = logging.getLogger(__name__)

class GeekJobParser:
    def __init__(self):
        self.base_url = "https://geekjob.ru/vacancies"
        self.ua = UserAgent()

    async def search(self, query: str, limit: int = 10) -> list:
        results = []
        params = {"q": query}
        headers = {
            "User-Agent": self.ua.random,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "ru-RU,ru;q=0.9",
        }
        
        try:
            logger.info(f"🔍 GeekJob: запрос '{query}'")
            timeout = aiohttp.ClientTimeout(total=45)
            
            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url, params=params, headers=headers, timeout=timeout) as resp:
                    logger.info(f"📡 GeekJob: статус {resp.status}")
                    if resp.status != 200:
                        text = await resp.text()
                        logger.error(f"Ответ: {text[:200]}")
                        return []
                    html = await resp.text()
            
            logger.info(f"📥 GeekJob: получено {len(html)} символов HTML")
            
            soup = BeautifulSoup(html, 'lxml')
            cards = soup.find_all("div", class_=re.compile(r"vacancy|job", re.I))
            if not cards:
                cards = soup.find_all("article")
            if not cards:
                cards = soup.find_all("li")
            
            logger.info(f"📦 GeekJob: найдено {len(cards)} карточек")
            
            if not cards:
                logger.warning(f"⚠️ GeekJob: не найдены карточки. Title: {soup.title.string if soup.title else 'None'}")
                return []
            
            for card in cards[:limit]:
                title_tag = card.find(["h2", "h3", "a"])
                if not title_tag:
                    continue
                title = title_tag.get_text(strip=True)
                
                link = ""
                a_tag = card.find("a", href=True)
                if a_tag:
                    link = a_tag["href"]
                    if not link.startswith("http"):
                        link = f"https://geekjob.ru{link}"
                
                company_tag = card.find(class_=re.compile(r"company|employer", re.I))
                company = company_tag.get_text(strip=True) if company_tag else "Не указано"
                
                if title and len(title) > 3:
                    results.append({
                        "title": title,
                        "company": company,
                        "salary": "Не указано",
                        "location": "Не указано",
                        "url": link,
                        "source": "geekjob.ru"
                    })
            
            logger.info(f"✅ GeekJob: {len(results)} вакансий")
            return results
            
        except Exception as e:
            logger.error(f"❌ GeekJob: {e}", exc_info=True)
            return []
