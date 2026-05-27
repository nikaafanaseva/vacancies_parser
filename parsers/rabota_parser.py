import aiohttp
import logging
import re
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

logger = logging.getLogger(__name__)


class RabotaParser:
    """Парсер Rabota.ru через поиск вакансий"""
    
    def __init__(self):
        self.base_url = "https://rabota.ru/search/vacancy"
        self.ua = UserAgent()

    def _get_headers(self):
        return {
            "User-Agent": self.ua.random,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "Referer": "https://rabota.ru/",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Cache-Control": "max-age=0",
        }

    async def search(self, query: str, limit: int = 10) -> list:
        results = []
        params = {"text": query}
        
        try:
            logger.info(f"🔍 Rabota.ru: поиск '{query}'")
            timeout = aiohttp.ClientTimeout(total=45)
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.base_url,
                    params=params,
                    headers=self._get_headers(),
                    timeout=timeout,
                    allow_redirects=True
                ) as resp:
                    logger.info(f"📡 Rabota.ru: статус {resp.status}")
                    if resp.status != 200:
                        text = await resp.text()
                        logger.error(f"Rabota.ru ответ: {text[:200]}")
                        return []
                    html = await resp.text()
            
            logger.info(f"📥 Rabota.ru: получено {len(html)} символов")
            
            soup = BeautifulSoup(html, 'lxml')
            
            # Rabota.ru использует разные классы для карточек
            cards = (
                soup.find_all("div", attrs={"data-qa": re.compile(r"vacancy", re.I)}) or
                soup.find_all("article", class_=re.compile(r"vacancy", re.I)) or
                soup.find_all("div", class_=re.compile(r"vacancy-card|vacancy_item|vacancyCard", re.I)) or
                soup.find_all("li", class_=re.compile(r"vacancy", re.I))
            )
            
            # Дополнительный поиск по всем ссылкам с вакансиями
            if not cards:
                cards = soup.find_all("a", href=re.compile(r"/vacancy/"))
                # Оборачиваем в список родительских элементов
                cards = [a.parent for a in cards if a.parent]
            
            logger.info(f"📦 Rabota.ru: найдено {len(cards)} карточек")
            
            if not cards:
                # Логируем title страницы для отладки
                title = soup.title.string if soup.title else "None"
                logger.warning(f"⚠️ Rabota.ru: карточки не найдены. Title: {title}")
                return []
            
            for card in cards[:limit]:
                try:
                    # Заголовок
                    title_tag = (
                        card.find(["h2", "h3"], class_=re.compile(r"title|name", re.I)) or
                        card.find("a", class_=re.compile(r"title|name|vacancy", re.I)) or
                        card.find(["h2", "h3"]) or
                        card.find("a", href=re.compile(r"/vacancy/"))
                    )
                    if not title_tag:
                        continue
                    
                    title = title_tag.get_text(strip=True)
                    
                    # Фильтруем мусор
                    if not title or len(title) < 5:
                        continue
                    if title.lower() in ["войти", "регистрация", "о компании", "контакты"]:
                        continue
                    
                    # Ссылка
                    link = ""
                    if title_tag.name == "a":
                        link = title_tag.get("href", "")
                    else:
                        a_tag = card.find("a", href=True)
                        if a_tag:
                            link = a_tag.get("href", "")
                    
                    if link and not link.startswith("http"):
                        link = f"https://rabota.ru{link}"
                    
                    # Компания
                    company_tag = (
                        card.find(class_=re.compile(r"company|employer", re.I)) or
                        card.find(attrs={"data-qa": re.compile(r"company|employer", re.I)})
                    )
                    company = company_tag.get_text(strip=True) if company_tag else "Не указано"
                    
                    # Зарплата
                    salary_tag = (
                        card.find(class_=re.compile(r"salary|money|compensation", re.I)) or
                        card.find(attrs={"data-qa": re.compile(r"salary|money", re.I)})
                    )
                    salary = salary_tag.get_text(strip=True) if salary_tag else "Не указано"
                    
                    # Город
                    location_tag = (
                        card.find(class_=re.compile(r"city|location|address", re.I)) or
                        card.find(attrs={"data-qa": re.compile(r"city|address", re.I)})
                    )
                    location = location_tag.get_text(strip=True) if location_tag else "Не указано"
                    
                    results.append({
                        "title": title,
                        "company": company,
                        "salary": salary,
                        "location": location,
                        "url": link,
                        "source": "rabota.ru"
                    })
                    logger.info(f"✅ Rabota.ru: {title[:50]}...")
                    
                except Exception as e:
                    logger.warning(f"⚠️ Rabota.ru: ошибка карточки: {e}")
                    continue
            
            logger.info(f"✅ Rabota.ru: обработано {len(results)} вакансий")
            return results
            
        except Exception as e:
            logger.error(f"❌ Rabota.ru: {e}", exc_info=True)
            return []
