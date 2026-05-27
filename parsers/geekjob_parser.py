import logging
from firecrawl import FirecrawlApp
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class GeekJobParser:
    def __init__(self, api_key: str):
        self.base_url = "https://geekjob.ru"
        self.app = FirecrawlApp(api_key=api_key)

    async def search(self, query: str, limit: int = 5) -> list:
        logger.info(f"🔍 GeekJob: поиск '{query}'")
        results = []
        
        try:
            url = f"{self.base_url}/?q={query.replace(' ', '+')}"
            logger.info(f"📡 GeekJob: {url}")
            
            response = self.app.scrape_url(url, params={'formats': ['markdown', 'html']})
            
            if not response.get('success'):
                logger.error("❌ GeekJob: ошибка скрейпинга")
                return results
            
            html = response.get('html', '')
            if not html:
                logger.warning("⚠️ GeekJob: пустой HTML")
                return results
            
            soup = BeautifulSoup(html, 'lxml')
            cards = soup.find_all(["article", "div"], class_=re.compile(r"vacancy|job", re.I))
            if not cards:
                cards = soup.find_all("li")
            
            for card in cards[:limit]:
                try:
                    title_tag = card.find("a")
                    if not title_tag:
                        continue
                    
                    title = title_tag.get_text(strip=True)
                    link = title_tag.get("href", "")
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
                            "source": "geekjob.ru"
                        })
                        logger.info(f"✅ GeekJob: {title[:40]}...")
                        
                except Exception as e:
                    logger.warning(f"⚠️ GeekJob: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"❌ GeekJob: {e}", exc_info=True)
        
        logger.info(f"📊 GeekJob: найдено {len(results)}")
        return results
