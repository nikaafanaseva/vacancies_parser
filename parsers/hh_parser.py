import aiohttp
import asyncio
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)


class HHParser:
    """
    Парсер вакансий через публичный API hh.ru.
    
    НЕ НУЖЕН Firecrawl! НЕ НУЖЕН BeautifulSoup!
    API сам возвращает готовый JSON с вакансиями.
    """

    def __init__(self, api_key: str = ""):
        # api_key не нужен — API публичный
        self.base_url = "https://api.hh.ru/vacancies"
        self.headers = {
            "User-Agent": "VacancyBot/1.0 (nika.afanaseva@gmail.com)",
            "Accept": "application/json",
        }

    async def search(self, query: str, limit: int = 5) -> List[Dict]:
        results = []
        try:
            params = {
                "text": query,
                "area": 1,              # 1 = Москва, 113 = вся Россия
                "per_page": limit,
                "page": 0,
                "order_by": "publication_time",
            }

            logger.info(f"HH API запрос: {query}")

            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.get(
                    self.base_url,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=15),
                ) as resp:
                    if resp.status != 200:
                        logger.error(f"HH API ошибка: статус {resp.status}")
                        return results

                    data = await resp.json()

            items = data.get("items", [])
            logger.info(f"HH API: получено {len(items)} вакансий из {data.get('found', 0)}")

            for item in items:
                # Зарплата
                salary = item.get("salary")
                salary_str = "Не указана"
                if salary:
                    parts = []
                    if salary.get("from"):
                        parts.append(f"от {salary['from']}")
                    if salary.get("to"):
                        parts.append(f"до {salary['to']}")
                    cur = {"RUR": "руб.", "USD": "$", "EUR": "€"}.get(
                        salary.get("currency", ""), salary.get("currency", "")
                    )
                    if parts:
                        salary_str = f"{' '.join(parts)} {cur}"

                # Город
                address = item.get("address")
                city = address.get("raw", "Не указано") if address else "Не указано"

                results.append({
                    "title": item.get("name", "Без названия"),
                    "company": item.get("employer", {}).get("name", "Не указано"),
                    "salary": salary_str,
                    "location": city,
                    "url": item.get("alternate_url", ""),
                    "source": "hh.ru",
                })

        except asyncio.TimeoutError:
            logger.error("HH API: таймаут")
        except Exception as e:
            logger.error(f"HH API ошибка: {e}", exc_info=True)

        logger.info(f"HH: найдено {len(results)}")
        return results
