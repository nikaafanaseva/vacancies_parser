if not settings.FIRECRAWL_API_KEY:
    logger.error("FIRECRAWL_API_KEY не установлен")
    sys.exit(1)

parsers = {
    "hh.ru": HHParser(api_key=settings.FIRECRAWL_API_KEY),
    "getmatch.ru": GetMatchParser(api_key=settings.FIRECRAWL_API_KEY),
    "geekjob.ru": GeekJobParser(api_key=settings.FIRECRAWL_API_KEY),
}
