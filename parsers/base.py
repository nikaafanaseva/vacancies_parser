import aiohttp
import asyncio
import json
import logging
from bs4 import BeautifulSoup
from typing import Optional, List, Dict
from fake_useragent import UserAgent
from tenacity import retry, stop_after_attempt, wait_exponential
from config import settings

logger = logging.getLogger(__name__)

class BaseParser:
    def __init__(self, source_name: str):
        self.source_name = source_name
        self.selectors = self._load_selectors()
        try:
            self.ua = UserAgent()
        except Exception:
            self.ua_str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        else:
            self.ua_str = self.ua.random

    def _load_selectors(self) -> Dict:
        try:
            with open("selectors.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get(self.source_name, {})
        except Exception as e:
            logger.error(f"Ошибка загрузки selectors.json для {self.source_name}: {e}")
            return {}

    def _get_headers(self) -> Dict[str, str]:
        return {
            "User-Agent": self.ua_str,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
            "From": settings.DEVELOPER_EMAIL
        }

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=2, max=5))
    async def _fetch_page(self, url: str) -> Optional[str]:
        async with aiohttp.ClientSession(headers=self._get_headers()) as session:
            try:
                async with session.get(url, timeout=30) as resp:
                    if resp.status == 200:
                        return await resp.text()
                    elif resp.status == 429:
                        logger.warning(f"{self.source_name}: Rate limit. Ждём 5 сек...")
                        await asyncio.sleep(5)
                        raise Exception("Rate limited")
                    else:
                        logger.warning(f"{self.source_name}: HTTP {resp.status}")
                        return None
            except aiohttp.ClientError as e:
                logger.error(f"{self.source_name} fetch error: {e}")
                raise

    def _parse_card(self, card, selectors: Dict) -> Optional[Dict]:
        try:
            def safe_text(selector: str) -> str:
                el = card.select_one(selector)
                return el.get_text(strip=True) if el else ""

            def safe_url(selector: str, prefix: str = "") -> str:
                el = card.select_one(selector)
                href = el.get("href", "") if el else ""
                return prefix + href if href and not href.startswith("http") else href

            title = safe_text(selectors.get("title", ""))
            if not title:
                return None

            return {
                "title": title,
                "company": safe_text(selectors.get("company", "")),
                "salary": safe_text(selectors.get("salary", "")) or "Не указана",
                "location": safe_text(selectors.get("location", "")),
                "url": safe_url(selectors.get("url", ""), selectors.get("url_prefix", "")),
                "source": self.source_name,
                "published": ""
            }
        except Exception as e:
            logger.warning(f"Ошибка парсинга карточки {self.source_name}: {e}")
            return None

    async def search(self, query: str, limit: int = 10) -> List[Dict]:
        if not self.selectors or "search_url" not in self.selectors:
            logger.error(f"Нет селекторов для {self.source_name}")
            return []

        url = self.selectors["search_url"].format(query=query.replace(" ", "+"))
        html = await self._fetch_page(url)
        if not html:
            return []

        soup = BeautifulSoup(html, "lxml")
        card_selector = self.selectors.get("vacancy_card", "")
        if not card_selector:
            return []

        cards = soup.select(card_selector)[:limit]
        results = []

        for card in cards:
            parsed = self._parse_card(card, self.selectors)
            if parsed:
                results.append(parsed)
            await asyncio.sleep(settings.REQUEST_DELAY)

        return results
