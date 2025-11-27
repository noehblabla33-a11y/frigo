"""
Helper pour la pagination des listes
"""

def paginate_query(query, page, per_page=20):
    """
    Pagine une requête SQLAlchemy
    
    Args:
        query: Query SQLAlchemy
        page: Numéro de page (commence à 1)
        per_page: Nombre d'éléments par page
    
    Returns:
        dict avec items, total, page, pages, has_prev, has_next
    """
    # S'assurer que page est au moins 1
    page = max(1, page)
    
    # Compter le total d'éléments
    total = query.count()
    
    # Calculer le nombre total de pages
    pages = (total + per_page - 1) // per_page if total > 0 else 1
    
    # S'assurer que page ne dépasse pas le nombre de pages
    page = min(page, pages)
    
    # Récupérer les éléments de la page
    items = query.limit(per_page).offset((page - 1) * per_page).all()
    
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


def get_page_range(current_page, total_pages, max_pages=5):
    """
    Calcule la plage de pages à afficher dans la pagination
    
    Args:
        current_page: Page actuelle
        total_pages: Nombre total de pages
        max_pages: Nombre maximum de pages à afficher
    
    Returns:
        Liste des numéros de page à afficher
    """
    if total_pages <= max_pages:
        return list(range(1, total_pages + 1))
    
    # Calculer le début et la fin de la plage
    half = max_pages // 2
    
    if current_page <= half:
        # Début de la pagination
        return list(range(1, max_pages + 1))
    elif current_page >= total_pages - half:
        # Fin de la pagination
        return list(range(total_pages - max_pages + 1, total_pages + 1))
    else:
        # Milieu de la pagination
        return list(range(current_page - half, current_page + half + 1))
