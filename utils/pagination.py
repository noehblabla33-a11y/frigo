"""
utils/pagination.py
Utilitaires de pagination pour l'application

✅ VERSION OPTIMISÉE - PHASE 2
- Fonction unique centralisée
- Support de la config Flask
- Gestion des cas limites
- Documentation complète
"""
from flask import current_app
from models.models import db
from sqlalchemy import func

def paginate_query(query, page, per_page=None):
    """
    Fonction de pagination réutilisable pour toutes les routes
    
    Args:
        query: Requête SQLAlchemy à paginer
        page (int): Numéro de page (commence à 1)
        per_page (int, optional): Nombre d'items par page
                                  Si None, utilise ITEMS_PER_PAGE_DEFAULT depuis config
    
    Returns:
        dict: Dictionnaire contenant les informations de pagination
            - items: Liste des items de la page actuelle
            - total: Nombre total d'items
            - page: Numéro de page actuel
            - pages: Nombre total de pages
            - per_page: Nombre d'items par page
            - has_prev: Booléen indiquant s'il y a une page précédente
            - has_next: Booléen indiquant s'il y a une page suivante
            - prev_page: Numéro de la page précédente (ou None)
            - next_page: Numéro de la page suivante (ou None)
    
    Exemples:
        >>> from models.models import Ingredient
        >>> query = Ingredient.query.order_by(Ingredient.nom)
        >>> pagination = paginate_query(query, page=1, per_page=24)
        >>> for ingredient in pagination['items']:
        ...     print(ingredient.nom)
        
        >>> # Avec config automatique
        >>> pagination = paginate_query(query, page=2)  # Utilise ITEMS_PER_PAGE_DEFAULT
    """
    # ============================================
    # RÉCUPÉRATION DES PARAMÈTRES
    # ============================================
    
    # Si per_page n'est pas spécifié, utiliser la config Flask
    if per_page is None:
        per_page = current_app.config.get('ITEMS_PER_PAGE_DEFAULT', 24)
    
    # ============================================
    # VALIDATION ET NORMALISATION
    # ============================================
    
    # S'assurer que per_page est au moins 1
    per_page = max(1, per_page)
    
    # S'assurer que page est au moins 1
    page = max(1, page)
    
    # ============================================
    # CALCUL DE LA PAGINATION
    # ============================================
    
    # Compter le nombre total d'items
    total = db.session.query(func.count()).select_from(query.subquery()).scalar()
    
    # Calculer le nombre total de pages
    if total > 0:
        pages = (total + per_page - 1) // per_page  # Division avec arrondi supérieur
    else:
        pages = 1  # Au moins une page même si vide
    
    # S'assurer que page ne dépasse pas le nombre de pages disponibles
    page = min(page, pages)
    
    # ============================================
    # RÉCUPÉRATION DES ITEMS
    # ============================================
    
    # Calculer l'offset pour la requête SQL
    offset = (page - 1) * per_page
    
    # Récupérer les items de la page actuelle
    items = query.limit(per_page).offset(offset).all()
    
    # ============================================
    # CONSTRUCTION DU RÉSULTAT
    # ============================================
    
    return {
        'items': items,
        'total': total,
        'page': page,
        'pages': pages,
        'per_page': per_page,
        'has_prev': page > 1,
        'has_next': page < pages,
        'prev_page': page - 1 if page > 1 else None,
        'next_page': page + 1 if page < pages else None
    }


def paginate_list(items, page, per_page):
    """
    Pagine une liste Python (pas une query SQLAlchemy).
    
    Utile quand on doit filtrer en Python après la requête DB,
    par exemple pour le filtre "en_stock" qui nécessite une vérification
    sur la relation stock de chaque ingrédient.
    
    Args:
        items: Liste d'éléments à paginer
        page: Numéro de page (1-indexed)
        per_page: Nombre d'éléments par page
    
    Returns:
        dict: Dictionnaire de pagination compatible avec les templates
    
    Exemple:
        >>> stocks = get_stocks_avec_ingredients()
        >>> pagination = paginate_list(stocks, page=2, per_page=24)
        >>> return render_template('frigo.html', 
        ...                        stocks=pagination['items'],
        ...                        pagination=pagination)
    """
    total = len(items)
    pages = (total + per_page - 1) // per_page if total > 0 else 1
    
    # Assurer que la page est dans les limites
    page = min(max(1, page), pages)
    
    # Calculer les indices de slice
    start = (page - 1) * per_page
    end = start + per_page
    
    return {
        'items': items[start:end],
        'total': total,
        'page': page,
        'pages': pages,
        'per_page': per_page,
        'has_prev': page > 1,
        'has_next': page < pages,
        'prev_page': page - 1 if page > 1 else None,
        'next_page': page + 1 if page < pages else None
    }
