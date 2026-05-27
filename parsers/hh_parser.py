import logging
import re
from firecrawl import FirecrawlApp
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class HHParser:
    def __init__(self, api_key: str):
        self.base_url = "https://hh.ru/search/vacancy"
        self.app = FirecrawlApp(api_key=api_key)

    async def search(self, query: str, limit: int = 5) -> list:
        logger.info(f"🔍 HHParser: поиск '{query}'")
        results = []
        
        try:
            url = f"{self.base_url}?text={query.replace(' ', '+')}"
            logger.info(f"📡 HH: {url}")
            
            response = self.app.scrape_url(url, params={'formats': ['markdown', 'html']})
            
            if not response.get('success'):
                logger.error(f"❌ HH: ошибка скрейпинга")
                return results
            
            html = response.get('html', '')
            if not html:
                logger.warning("⚠️ HH: пустой HTML")
                return results
            
            soup = BeautifulSoup(html, 'lxml')
            cards = soup.find_all("div", class_="vacancy-serp-item")
            
            for card in cards[:limit]:
                try:
                    title_tag = card.find("a", class_="bloko-link")
                    if not title_tag:
                        continue
                    
                    title = title_tag.get_text(strip=True)
                    link = title_tag.get("href", "")
                    if link and not link.startswith("http"):
                        link = f"https://hh.ru{link}"
                    
                    company_tag = card.find("span", class_="bloko-link")
                    company = company_tag.get_text(strip=True) if company_tag else "Не указано"
                    
                    salary_tag = card.find("span", attrs={"data-qa": "vacancy-serp__vacancy-compensation"})
                    salary = salary_tag.get_text(strip=True) if salary_tag else "Не указано"
                    
                    city_tag = card.find("span", attrs={"data-qa": "vacancy-serp__vacancy-address"})
                    city = city_tag.get_text(strip=True) if city_tag else "Не указано"
                    
                    results.append({
                        "title": title,
                        "company": company,
                        "salary": salary,
                        "location": city,
                        "url": link,
                        "source": "hh.ru"
                    })
                    logger.info(f"✅ HH: {title[:40]}...")
                    
                except Exception as e:
                    logger.warning(f"⚠️ HH: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"❌ HHParser: {e}", exc_info=True)
        
        logger.info(f"📊 HH: найдено {len(results)}")
        return results
