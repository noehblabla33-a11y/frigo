"""
Scrapers pour différentes sources de prix
"""
from price_scraper.scrapers.base_scraper import BaseScraper
from price_scraper.scrapers.openfoodfacts import OpenFoodFactsScraper

__all__ = ['BaseScraper', 'OpenFoodFactsScraper']
