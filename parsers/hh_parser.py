import aiohttp
import asyncio
import random
from bs4 import BeautifulSoup
import logging
import urllib.parse

logger = logging.getLogger(__name__)

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
]

async def get_hh_vacancies(keyword: str):
    """Парсинг вакансий с hh.ru через HTML-парсинг (без API)"""
    vacancies = []
    
    encoded_keyword = urllib.parse.quote(keyword)
    url = f"https://hh.ru/search/vacancy?text={encoded_keyword}&area=113&items_on_page=10"
    
    headers = {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
        'Referer': 'https://hh.ru/',
    }
    
    logger.info(f"HH парсинг: {keyword}")
    
    try:
        await asyncio.sleep(random.uniform(1, 2))
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=15) as response:
                
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    items = soup.find_all('div', {'data-qa': 'vacancy-serp__vacancy'})
                    
                    if not items:
                        items = soup.find_all('div', class_='serp-item')
                    
                    for item in items[:5]:
                        try:
                            title_elem = item.find('a', {'data-qa': 'vacancy-serp__vacancy-title'})
                            if not title_elem:
                                title_elem = item.find('a', class_='serp-item__title')
                            
                            if title_elem:
                                title = title_elem.text.strip()
                                link = title_elem.get('href')
                            else:
                                continue
                            
                            company_elem = item.find('div', {'data-qa': 'vacancy-serp__vacancy-employer'})
                            if not company_elem:
                                company_elem = item.find('div', class_='vacancy-serp-item__meta-info-company')
                            company = company_elem.text.strip() if company_elem else 'Не указана'
                            
                            salary_elem = item.find('span', {'data-qa': 'vacancy-serp__vacancy-compensation'})
                            salary = salary_elem.text.strip() if salary_elem else 'Не указана'
                            
                            address_elem = item.find('div', {'data-qa': 'vacancy-serp__vacancy-address'})
                            city = address_elem.text.strip() if address_elem else 'Не указан'
                            
                            vacancies.append({
                                'title': title,
                                'company': company,
                                'salary': salary,
                                'city': city,
                                'url': link,
                                'source': 'hh.ru'
                            })
                        except Exception as e:
                            logger.error(f"Ошибка парсинга: {e}")
                            continue
                    
                    logger.info(f"HH: найдено {len(vacancies)} вакансий")
                    return vacancies
                    
                else:
                    logger.error(f"HH ошибка: статус {response.status}")
                    return []
                    
    except asyncio.TimeoutError:
        logger.error("HH таймаут")
        return []
    except Exception as e:
        logger.error(f"HH ошибка: {e}")
        return []
