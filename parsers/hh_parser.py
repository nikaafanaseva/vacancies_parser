import aiohttp
import logging
import asyncio

logger = logging.getLogger(__name__)

class HHParser:
    def __init__(self):
        self.api_url = "https://api.hh.ru/vacancies"
        # Максимально "человеческие" заголовки
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Cache-Control": "max-age=0"
        }

    async def search(self, query: str, limit: int = 10) -> list:
        results = []
        params = {
            "text": query,
            "per_page": min(limit, 20),
            "order_by": "publication_time",
            "page": 0,
        }
        
        # Пробуем 3 раза с увеличенным таймаутом
        for attempt in range(3):
            try:
                logger.info(f"🔍 HH API: попытка {attempt + 1}/3 для '{query}'")
                
                timeout = aiohttp.ClientTimeout(total=60)  # 60 секунд!
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        self.api_url,
                        params=params,
                        headers=self.headers,
                        timeout=timeout
                    ) as resp:
                        logger.info(f"📡 HH API: статус {resp.status}")
                        
                        if resp.status == 403:
                            logger.error("❌ HH API: 403 Forbidden (блокировка IP)")
                            return []
                        if resp.status == 429:
                            logger.warning("⚠️ HH API: слишком много запросов, ждём...")
                            await asyncio.sleep(5)
                            continue
                        if resp.status != 200:
                            logger.error(f"❌ HH API: статус {resp.status}")
                            text = await resp.text()
                            logger.error(f"Ответ: {text[:200]}")
                            return []
                        
                        data = await resp.json()
                        logger.info(f"✅ HH API: получено {len(data.get('items', []))} вакансий")
                        
                        for item in data.get("items", []):
                            salary = "Не указано"
                            if item.get("salary"):
                                s = item["salary"]
                                parts = []
                                if s.get("from"): parts.append(f"от {s['from']}")
                                if s.get("to"): parts.append(f"до {s['to']}")
                                if s.get("currency"): parts.append(s["currency"])
                                if parts: salary = " ".join(parts)

                            results.append({
                                "title": item.get("name", "Вакансия"),
                                "company": item.get("employer", {}).get("name", "Не указано") if item.get("employer") else "Не указано",
                                "salary": salary,
                                "location": item.get("area", {}).get("name", "Не указано"),
                                "url": item.get("alternate_url", ""),
                                "source": "hh.ru"
                            })
                        
                        logger.info(f"✅ HH: обработано {len(results)}")
                        return results
                        
            except asyncio.TimeoutError:
                logger.warning(f"⚠️ HH API: таймаут на попытке {attempt + 1}")
                if attempt < 2:
                    await asyncio.sleep(2)
                    continue
            except Exception as e:
                logger.error(f"❌ HH API ошибка: {e}", exc_info=True)
                if attempt < 2:
                    await asyncio.sleep(2)
                    continue
        
        logger.error("❌ HH API: все попытки не удались")
        return []
