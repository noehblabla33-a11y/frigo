"""
Module de collecte et gestion des prix d'ingrédients
"""
from price_scraper.config import ScraperConfig
from price_scraper.models import PrixHistorique, SourcePrix, MappingIngredient

__version__ = '1.0.0'
__all__ = ['ScraperConfig', 'PrixHistorique', 'SourcePrix', 'MappingIngredient']
