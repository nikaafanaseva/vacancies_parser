import aiohttp
import asyncio
import random
from bs4 import BeautifulSoup
import logging
import urllib.parse

logger = logging.getLogger(__name__)

async def get_getmatch_vacancies(keyword: str):
    """Парсинг вакансий с getmatch.ru"""
    vacancies = []
    
    encoded_keyword = urllib.parse.quote(keyword)
    url = f"https://getmatch.ru/vacancies?search={encoded_keyword}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    }
    
    logger.info(f"GetMatch URL: {url}")
    
    try:
        await asyncio.sleep(random.uniform(0.5, 1.5))
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=15) as response:
                
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    cards = soup.find_all('div', class_='vacancy-card')
                    if not cards:
                        cards = soup.find_all('div', class_='vacancy-item')
                    
                    for card in cards[:5]:
                        try:
                            title_elem = card.find('a', class_='vacancy-title')
                            if not title_elem:
                                title_elem = card.find('h3')
                            
                            if title_elem:
                                title = title_elem.text.strip()
                                link = title_elem.get('href', '')
                                if link and not link.startswith('http'):
                                    link = 'https://getmatch.ru' + link
                            else:
                                continue
                            
                            company_elem = card.find('div', class_='company-name')
                            company = company_elem.text.strip() if company_elem else 'Не указана'
                            
                            vacancies.append({
                                'title': title,
                                'company': company,
                                'salary': 'Не указана',
                                'city': 'Не указан',
                                'url': link,
                                'source': 'getmatch.ru'
                            })
                        except Exception as e:
                            logger.error(f"Ошибка GetMatch: {e}")
                            continue
                    
                else:
                    logger.warning(f"GetMatch статус: {response.status}")
                    
    except Exception as e:
        logger.error(f"GetMatch ошибка: {e}")
    
    logger.info(f"GetMatch: найдено {len(vacancies)}")
    return vacancies
