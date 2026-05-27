import logging
from firecrawl import FirecrawlApp
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class GetMatchParser:
    def __init__(self, api_key: str):
        self.base_url = "https://getmatch.ru/vacancies"
        self.app = FirecrawlApp(api_key=api_key)

    async def search(self, query: str, limit: int = 5) -> list:
        logger.info(f"🔍 GetMatch: поиск '{query}'")
        results = []
        
        try:
            url = f"{self.base_url}?search={query.replace(' ', '+')}"
            logger.info(f"📡 GetMatch: {url}")
            
            response = self.app.scrape_url(url, params={'formats': ['markdown', 'html']})
            
            if not response.get('success'):
                logger.error("❌ GetMatch: ошибка скрейпинга")
                return results
            
            html = response.get('html', '')
            if not html:
                logger.warning("⚠️ GetMatch: пустой HTML")
                return results
            
            soup = BeautifulSoup(html, 'lxml')
            cards = soup.find_all(["article", "div"], class_=re.compile(r"vacancy|job", re.I))
            if not cards:
                cards = soup.find_all("li")
            
            for card in cards[:limit]:
                try:
                    title_tag = card.find(["h2", "h3", "a"])
                    if not title_tag:
                        continue
                    
                    title = title_tag.get_text(strip=True)
                    link_tag = card.find("a")
                    link = link_tag.get("href", "") if link_tag else ""
                    if link and not link.startswith("http"):
                        link = f"https://getmatch.ru{link}"
                    
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
                            "source": "getmatch.ru"
                        })
                        logger.info(f"✅ GetMatch: {title[:40]}...")
                        
                except Exception as e:
                    logger.warning(f"⚠️ GetMatch: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"❌ GetMatch: {e}", exc_info=True)
        
        logger.info(f"📊 GetMatch: найдено {len(results)}")
        return results
