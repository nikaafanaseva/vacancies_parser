import aiohttp
import logging
import re
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

logger = logging.getLogger(__name__)

class GetMatchParser:
    def __init__(self):
        self.base_url = "https://getmatch.ru/vacancies"
        self.ua = UserAgent()

    async def search(self, query: str, limit: int = 10) -> list:
        results = []
        params = {"search": query}
        headers = {"User-Agent": self.ua.random}
        
        try:
            logger.info(f"🔍 GetMatch: запрос '{query}'")
            timeout = aiohttp.ClientTimeout(total=30)
            
            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url, params=params, headers=headers, timeout=timeout) as resp:
                    logger.info(f"📡 GetMatch: статус {resp.status}")
                    if resp.status != 200:
                        return []
                    html = await resp.text()
            
            logger.info(f"📥 GetMatch: получено {len(html)} символов")
            
            soup = BeautifulSoup(html, 'lxml')
            
            # Ищем именно карточки вакансий, а не меню
            cards = soup.find_all("article", class_=re.compile(r"vacancy", re.I))
            if not cards:
                cards = soup.find_all("div", {"data-testid": re.compile(r"vacancy", re.I)})
            if not cards:
                # Если карточки не найдены, логируем и возвращаем пустой список
                logger.warning("⚠️ GetMatch: карточки вакансий не найдены в HTML")
                return []
            
            logger.info(f"📦 GetMatch: найдено {len(cards)} карточек вакансий")
            
            for card in cards[:limit]:
                title_tag = card.find(["h2", "h3", "a"], class_=re.compile(r"title|name", re.I))
                if not title_tag:
                    continue
                
                title = title_tag.get_text(strip=True)
                
                # Проверяем, что это действительно вакансия, а не элемент меню
                if len(title) < 5 or title.lower() in ["зарплаты", "каталог", "работодателям", "разместить вакансию"]:
                    continue
                
                link = ""
                a_tag = card.find("a", href=True)
                if a_tag:
                    link = a_tag["href"]
                    if not link.startswith("http"):
                        link = f"https://getmatch.ru{link}"
                
                company_tag = card.find(class_=re.compile(r"company|employer", re.I))
                company = company_tag.get_text(strip=True) if company_tag else "Не указано"
                
                salary_tag = card.find(class_=re.compile(r"salary", re.I))
                salary = salary_tag.get_text(strip=True) if salary_tag else "Не указано"
                
                results.append({
                    "title": title,
                    "company": company,
                    "salary": salary,
                    "location": "Не указано",
                    "url": link,
                    "source": "getmatch.ru"
                })
            
            logger.info(f"✅ GetMatch: {len(results)} вакансий")
            return results
            
        except Exception as e:
            logger.error(f"❌ GetMatch: {e}", exc_info=True)
            return []
