"""
Configuration pour le système de collecte de prix
"""
import os

class ScraperConfig:
    """Configuration générale pour les scrapers"""
    
    # Chemins
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    LOG_DIR = os.path.join(BASE_DIR, 'logs')
    
    # Configuration des requêtes HTTP
    REQUEST_TIMEOUT = 10  # secondes
    MAX_RETRIES = 3
    RETRY_DELAY = 2  # secondes
    
    # User-Agent pour les requêtes
    USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    
    # Configuration Open Food Facts
    OPENFOODFACTS_API_URL = 'https://world.openfoodfacts.org/api/v2'
    OPENFOODFACTS_SEARCH_URL = 'https://world.openfoodfacts.org/cgi/search.pl'
    OPENFOODFACTS_USER_AGENT = 'MonFrigoCourses - Price Scraper - Contact: votre-email@example.com'
    
    # Limites de requêtes (pour éviter le rate limiting)
    REQUEST_DELAY = 1  # secondes entre chaque requête
    MAX_REQUESTS_PER_MINUTE = 50
    
    # Configuration des prix
    PRIX_MIN = 0.01  # Prix minimum acceptable (€)
    PRIX_MAX = 1000.0  # Prix maximum acceptable (€)
    
    # Score de confiance
    CONFIANCE_MIN = 0.3  # Score minimum pour considérer un prix valide
    
    # Seuils de variation de prix
    VARIATION_MAX_HAUSSE = 2.0  # 200% d'augmentation max
    VARIATION_MAX_BAISSE = 0.5  # 50% de baisse max
    
    # Mapping des catégories
    CATEGORIES_MAPPING = {
        'Légumes': ['vegetables', 'legumes', 'vegetable'],
        'Fruits': ['fruits', 'fruit'],
        'Viandes': ['meat', 'viandes', 'poultry', 'beef', 'pork'],
        'Poissons': ['fish', 'poisson', 'seafood'],
        'Produits laitiers': ['dairy', 'milk', 'cheese', 'yogurt', 'lait', 'fromage'],
        'Féculents': ['pasta', 'rice', 'bread', 'cereals', 'pates', 'riz', 'pain'],
        'Épices et herbes': ['spices', 'herbs', 'epices', 'herbes'],
        'Condiments': ['condiments', 'sauces'],
        'Boissons': ['beverages', 'drinks', 'boissons'],
        'Boulangerie': ['bakery', 'boulangerie'],
        'Autres': ['other', 'autres']
    }
    
    # Configuration des sources
    SOURCES_CONFIG = {
        'openfoodfacts': {
            'actif': True,
            'priorite': 80,
            'fiabilite': 0.85,
            'description': 'Base de données collaborative Open Food Facts'
        },
        'manuel': {
            'actif': True,
            'priorite': 100,
            'fiabilite': 1.0,
            'description': 'Prix saisis manuellement par l\'utilisateur'
        }
    }
    
    # Unités de conversion
    UNITES_CONVERSION = {
        'kg': {'g': 1000, 'kg': 1},
        'g': {'g': 1, 'kg': 0.001},
        'l': {'ml': 1000, 'l': 1, 'cl': 100},
        'ml': {'ml': 1, 'l': 0.001, 'cl': 0.1},
        'cl': {'ml': 10, 'l': 0.01, 'cl': 1},
        'unité': {'unité': 1}
    }
    
    @staticmethod
    def create_log_dir():
        """Crée le répertoire de logs s'il n'existe pas"""
        os.makedirs(ScraperConfig.LOG_DIR, exist_ok=True)
