import aiohttp
import logging
import asyncio
import re
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class HHParser:
    """
    Парсер HeadHunter через ОФИЦИАЛЬНОЕ API.
    Не требует регистрации, токенов и ключей.
    Нужен только корректный User-Agent.
    Документация: https://github.com/hhru/api
    """
    
    def __init__(self):
        # ВАЖНО: User-Agent должен быть осмысленным, иначе 403 ошибка
        self.headers = {
            "User-Agent": "VacancyBot/1.0 (vacancies_parser; contact@example.com)",
            "Accept": "application/json",
            "Accept-Language": "ru-RU,ru;q=0.9",
        }
        self.api_url = "https://api.hh.ru/vacancies"

    def _clean_html(self, html_text: str) -> str:
        """Убирает HTML-теги из описания вакансии"""
        if not html_text:
            return ""
        soup = BeautifulSoup(html_text, 'lxml')
        return soup.get_text(separator=' ', strip=True)

    def _format_salary(self, salary: dict) -> str:
        """Форматирует зарплату из API"""
        if not salary:
            return "Не указано"
        
        parts = []
        if salary.get("from"):
            parts.append(f"от {salary['from']:,}".replace(",", " "))
        if salary.get("to"):
            parts.append(f"до {salary['to']:,}".replace(",", " "))
        
        if not parts:
            return "Не указано"
        
        result = " ".join(parts)
        currency = salary.get("currency", "")
        if currency:
            symbols = {"RUR": "₽", "RUB": "₽", "USD": "$", "EUR": "€", "BYR": "Br"}
            result += f" {symbols.get(currency, currency)}"
        
        if salary.get("gross"):
            result += " (до вычета налогов)"
        
        return result

    async def search(self, query: str, limit: int = 10) -> list:
        """Поиск вакансий через API hh.ru"""
        results = []
        
        params = {
            "text": query,
            "per_page": min(limit, 100),  # API максимум 100 за раз
            "page": 0,
            "order_by": "publication_time",  # Сначала новые
        }
        
        try:
            logger.info(f"🔍 HH.ru API: поиск '{query}'")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.api_url,
                    params=params,
                    headers=self.headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as resp:
                    if resp.status == 403:
                        logger.error("❌ HH.ru: 403 Forbidden. Проверь User-Agent!")
                        return []
                    if resp.status == 429:
                        logger.error("❌ HH.ru: слишком много запросов (Rate Limit)")
                        return []
                    if resp.status != 200:
                        logger.error(f"❌ HH.ru: HTTP {resp.status}")
                        return []
                    
                    data = await resp.json()
            
            logger.info(f"📦 HH.ru: API вернул {data.get('found', 0)} вакансий")
            
            items = data.get("items", [])
            for item in items[:limit]:
                try:
                    salary = self._format_salary(item.get("salary"))
                    
                    # Локация
                    location = "Не указано"
                    area = item.get("area")
                    if area:
                        location = area.get("name", "Не указано")
                    
                    # Компания
                    employer = item.get("employer")
                    company = employer.get("name", "Не указано") if employer else "Не указано"
                    
                    # Убираем HTML из сниппета
                    snippet = item.get("snippet", {}) or {}
                    responsibility = snippet.get("responsibility", "") or ""
                    requirement = snippet.get("requirement", "") or ""
                    description = f"{responsibility} {requirement}".strip()
                    
                    results.append({
                        "title": item.get("name", "Вакансия"),
                        "company": company,
                        "salary": salary,
                        "location": location,
                        "url": item.get("alternate_url", ""),
                        "source": "hh.ru",
                        "description": description[:200] + "..." if len(description) > 200 else description,
                    })
                except Exception as e:
                    logger.warning(f"⚠️ HH: ошибка обработки вакансии: {e}")
                    continue
            
            logger.info(f"✅ HH.ru: обработано {len(results)} вакансий")
            
        except asyncio.TimeoutError:
            logger.error("❌ HH.ru: таймаут запроса")
        except Exception as e:
            logger.error(f"❌ HH.ru: {e}", exc_info=True)
        
        return results
