"""
utils/cache.py
Système de cache centralisé pour l'application

✅ OPTIMISATION TECHNIQUE - Flask-Caching
- Cache en mémoire (SimpleCache) pour usage local
- Décorateurs pour mettre en cache les requêtes lourdes
- Fonctions d'invalidation du cache

INSTALLATION:
    pip install Flask-Caching

USAGE:
    from utils.cache import cache, cached_query, invalidate_cache
    
    # Dans une route ou fonction
    @cached_query('ma_cle', timeout=300)
    def ma_fonction_lourde():
        return db.session.query(...).all()
    
    # Invalider après modification
    invalidate_cache('ma_cle')
"""
from functools import wraps
from flask import current_app
from flask_caching import Cache
from datetime import datetime, timedelta, timezone

# Instance globale du cache
cache = Cache()


def init_cache(app):
    """
    Initialise le cache avec l'application Flask.
    
    À appeler dans create_app() après la configuration.
    
    Args:
        app: Instance Flask
    """
    cache.init_app(app)
    app.logger.info('✅ Flask-Caching initialisé')


# ============================================
# DÉCORATEURS DE CACHE
# ============================================

def cached_query(key_prefix, timeout=300):
    """
    Décorateur pour mettre en cache le résultat d'une fonction.
    
    Args:
        key_prefix: Préfixe de la clé de cache
        timeout: Durée de vie en secondes (défaut: 5 minutes)
    
    Usage:
        @cached_query('categories_count', timeout=600)
        def get_categories_count():
            return db.session.query(...).all()
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            # Construire la clé avec les arguments
            cache_key = f"{key_prefix}:{hash(str(args) + str(kwargs))}"
            
            # Essayer de récupérer du cache
            result = cache.get(cache_key)
            if result is not None:
                return result
            
            # Exécuter la fonction et mettre en cache
            result = f(*args, **kwargs)
            cache.set(cache_key, result, timeout=timeout)
            return result
        
        # Stocker le préfixe pour l'invalidation
        wrapper._cache_prefix = key_prefix
        return wrapper
    return decorator


def memoize_for_request(f):
    """
    Décorateur qui met en cache le résultat pour la durée de la requête.
    Utile pour éviter les calculs répétés dans une même requête.
    
    Usage:
        @memoize_for_request
        def calculer_stats():
            return {...}
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        from flask import g
        
        cache_key = f"_memoize_{f.__name__}_{hash(str(args) + str(kwargs))}"
        
        if not hasattr(g, '_memoize_cache'):
            g._memoize_cache = {}
        
        if cache_key not in g._memoize_cache:
            g._memoize_cache[cache_key] = f(*args, **kwargs)
        
        return g._memoize_cache[cache_key]
    return wrapper


# ============================================
# INVALIDATION DU CACHE
# ============================================

def invalidate_cache(key_prefix):
    """
    Invalide toutes les entrées de cache avec un préfixe donné.
    
    Note: Avec SimpleCache, on ne peut pas lister les clés,
    donc on utilise cache.clear() pour un préfixe spécifique
    via une approche par pattern.
    
    Args:
        key_prefix: Préfixe des clés à invalider
    """
    # Avec SimpleCache, la meilleure approche est de supprimer
    # les clés connues ou de clear tout le cache
    try:
        cache.delete_memoized(key_prefix)
    except:
        pass


def clear_all_cache():
    """
    Vide complètement le cache.
    À utiliser avec précaution.
    """
    cache.clear()
    current_app.logger.info('🗑️ Cache entièrement vidé')


def invalidate_ingredients_cache():
    """Invalide le cache lié aux ingrédients."""
    keys = [
        'categories_count',
        'ingredients_list',
        'ingredients_all',
        'dashboard_stats'
    ]
    for key in keys:
        cache.delete(key)


def invalidate_recettes_cache():
    """Invalide le cache lié aux recettes."""
    keys = [
        'recettes_list',
        'recettes_realisables',
        'dashboard_stats',
        'recommendations'
    ]
    for key in keys:
        cache.delete(key)


def invalidate_stock_cache():
    """Invalide le cache lié au stock/frigo."""
    keys = [
        'stock_frigo',
        'stock_valeur',
        'dashboard_stats',
        'recettes_realisables'
    ]
    for key in keys:
        cache.delete(key)


def invalidate_courses_cache():
    """Invalide le cache lié aux courses."""
    keys = [
        'courses_list',
        'courses_budget',
        'dashboard_stats'
    ]
    for key in keys:
        cache.delete(key)


# ============================================
# FONCTIONS CACHÉES PRÊTES À L'EMPLOI
# ============================================

@cache.memoize(timeout=300)
def get_categories_count_cached():
    """
    Retourne le comptage des ingrédients par catégorie (caché 5 min).

    Retour:
        Dict {categorie: count}
    """
    from utils.queries_optimized import get_categories_count
    return get_categories_count()


@cache.memoize(timeout=300)
def get_all_ingredients_cached():
    """
    Retourne tous les ingrédients ordonnés par nom (caché 5 min).

    Retour:
        Liste d'Ingredient
    """
    from utils.queries_optimized import get_all_ingredients
    return get_all_ingredients(with_stock=False, with_saisons=False)


@cache.memoize(timeout=60)
def get_stock_value_cached():
    """
    Calcule la valeur totale du stock (caché 1 min).

    Retour:
        float: Valeur totale en euros
    """
    from sqlalchemy.orm import joinedload
    from models.models import StockFrigo

    stocks = StockFrigo.query.options(
        joinedload(StockFrigo.ingredient)
    ).all()

    return round(sum(
        stock.ingredient.calculer_prix(stock.quantite)
        for stock in stocks
    ), 2)


@cache.memoize(timeout=120)
def get_recettes_count_cached():
    """
    Retourne les compteurs de recettes (caché 2 min).
    """
    from models.models import Recette, RecettePlanifiee
    
    return {
        'total': Recette.query.count(),
        'planifiees': RecettePlanifiee.query.filter_by(preparee=False).count()
    }


@cache.memoize(timeout=300)
def get_historique_stats_cached():
    """
    Calcule les statistiques de l'historique (caché 5 min).
    """
    from sqlalchemy import func, desc
    from datetime import datetime, timedelta
    from models.models import db, RecettePlanifiee, Recette, IngredientRecette, Ingredient
    
    maintenant = datetime.now(timezone.utc)
    debut_mois = maintenant.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    debut_semaine = maintenant - timedelta(days=maintenant.weekday())
    
    # Stats globales
    total = RecettePlanifiee.query.filter_by(preparee=True).count()
    
    mois = RecettePlanifiee.query.filter(
        RecettePlanifiee.preparee == True,
        RecettePlanifiee.date_preparation >= debut_mois
    ).count()
    
    semaine = RecettePlanifiee.query.filter(
        RecettePlanifiee.preparee == True,
        RecettePlanifiee.date_preparation >= debut_semaine
    ).count()
    
    return {
        'total': total,
        'mois': mois,
        'semaine': semaine
    }


# ============================================
# CONFIGURATION PAR DÉFAUT
# ============================================

DEFAULT_CACHE_CONFIG = {
    'CACHE_TYPE': 'SimpleCache',  # Cache en mémoire (parfait pour local)
    'CACHE_DEFAULT_TIMEOUT': 300,  # 5 minutes par défaut
    'CACHE_THRESHOLD': 500,  # Nombre max d'items en cache
}


def get_cache_config(app_config=None):
    """
    Retourne la configuration du cache adaptée à l'environnement.
    
    Args:
        app_config: Configuration de l'application (optionnel)
    
    Returns:
        Dict de configuration pour Flask-Caching
    """
    config = DEFAULT_CACHE_CONFIG.copy()
    
    if app_config:
        # En production, on pourrait utiliser Redis ou Memcached
        if app_config.get('ENV') == 'production':
            # Pour l'instant, on reste sur SimpleCache
            # mais on pourrait configurer Redis ici
            pass
        
        # Permettre override via config
        if 'CACHE_TYPE' in app_config:
            config['CACHE_TYPE'] = app_config['CACHE_TYPE']
        if 'CACHE_DEFAULT_TIMEOUT' in app_config:
            config['CACHE_DEFAULT_TIMEOUT'] = app_config['CACHE_DEFAULT_TIMEOUT']
    
    return config
