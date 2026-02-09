"""
utils/database.py
Context managers et décorateurs pour la gestion des transactions de base de données
"""
from contextlib import contextmanager
from functools import wraps
from flask import flash
from models.models import db
import logging

logger = logging.getLogger(__name__)


# ============================================
# CONTEXT MANAGER BASIQUE
# ============================================

@contextmanager
def db_transaction():
    """
    Context manager pour gérer automatiquement les transactions
    
    Usage:
        with db_transaction():
            ingredient = Ingredient(nom='Tomate')
            db.session.add(ingredient)
            # Commit automatique si pas d'erreur
            # Rollback automatique en cas d'erreur
    
    Example:
        try:
            with db_transaction():
                recette = Recette(nom='Tarte')
                db.session.add(recette)
                # Si erreur ici, rollback automatique
        except Exception as e:
            flash(f'Erreur : {e}', 'danger')
    """
    try:
        yield db.session
        db.session.commit()
        logger.debug("✅ Transaction committée avec succès")
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Transaction annulée : {e}")
        raise  # Re-lever l'exception pour que l'appelant puisse la gérer


# ============================================
# CONTEXT MANAGER AVEC FLASH MESSAGE
# ============================================

@contextmanager
def db_transaction_with_flash(success_message=None, error_message=None):
    """
    Context manager avec gestion automatique des messages flash
    
    Args:
        success_message: Message en cas de succès (None = pas de message)
        error_message: Message en cas d'erreur (None = message par défaut)
    
    Usage:
        with db_transaction_with_flash(
            success_message='Ingrédient ajouté !',
            error_message='Erreur lors de l\'ajout'
        ):
            ingredient = Ingredient(nom='Tomate')
            db.session.add(ingredient)
    
    Example:
        with db_transaction_with_flash('Recette créée !'):
            recette = Recette(nom='Tarte')
            db.session.add(recette)
            # Message flash automatique si succès
    """
    try:
        yield db.session
        db.session.commit()
        
        if success_message:
            flash(success_message, 'success')
        
        logger.debug(f"✅ Transaction réussie : {success_message or 'OK'}")
        
    except Exception as e:
        db.session.rollback()
        
        error_msg = error_message or f"Une erreur est survenue : {str(e)}"
        flash(error_msg, 'danger')
        
        logger.error(f"❌ Transaction échouée : {e}")
        raise


# ============================================
# CONTEXT MANAGER AVEC RETRY
# ============================================

@contextmanager
def db_transaction_with_retry(max_retries=3, success_message=None):
    """
    Context manager avec système de retry automatique
    
    Args:
        max_retries: Nombre maximum de tentatives
        success_message: Message de succès (optionnel)
    
    Usage:
        with db_transaction_with_retry(max_retries=3):
            ingredient = Ingredient(nom='Tomate')
            db.session.add(ingredient)
            # Retry automatique en cas d'erreur de concurrence
    """
    from sqlalchemy.exc import OperationalError, IntegrityError
    import time
    
    last_exception = None
    
    for attempt in range(max_retries):
        try:
            yield db.session
            db.session.commit()
            
            if success_message:
                flash(success_message, 'success')
            
            logger.debug(f"✅ Transaction réussie (tentative {attempt + 1}/{max_retries})")
            return  # Succès, on sort
            
        except (OperationalError, IntegrityError) as e:
            db.session.rollback()
            last_exception = e
            
            logger.warning(f"⚠️ Tentative {attempt + 1}/{max_retries} échouée : {e}")
            
            if attempt < max_retries - 1:
                time.sleep(0.1 * (attempt + 1))  # Backoff exponentiel
            else:
                # Dernière tentative échouée
                flash(f"Erreur après {max_retries} tentatives", 'danger')
                raise last_exception
        
        except Exception as e:
            # Erreur non-récupérable
            db.session.rollback()
            logger.error(f"❌ Erreur non-récupérable : {e}")
            flash(f"Erreur : {str(e)}", 'danger')
            raise


# ============================================
# DÉCORATEUR POUR LES ROUTES
# ============================================

def with_db_transaction(success_message=None, error_message=None):
    """
    Décorateur pour entourer une route d'une transaction automatique
    
    Args:
        success_message: Message de succès (optionnel)
        error_message: Message d'erreur (optionnel)
    
    Usage:
        @ingredients_bp.route('/ajouter', methods=['POST'])
        @with_db_transaction(success_message='Ingrédient ajouté !')
        def ajouter():
            ingredient = Ingredient(nom=request.form.get('nom'))
            db.session.add(ingredient)
            return redirect(url_for('ingredients.liste'))
    
    Note:
        Le commit est automatique à la fin de la fonction
        Le rollback est automatique en cas d'erreur
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                db.session.commit()
                
                if success_message:
                    flash(success_message, 'success')
                
                logger.debug(f"✅ Transaction de {func.__name__} réussie")
                return result
                
            except Exception as e:
                db.session.rollback()
                
                error_msg = error_message or f"Erreur dans {func.__name__}: {str(e)}"
                flash(error_msg, 'danger')
                
                logger.error(f"❌ Transaction de {func.__name__} échouée : {e}")
                raise
        
        return wrapper
    return decorator


# ============================================
# HELPER : COMMIT SAFE
# ============================================

def safe_commit():
    """
    Fonction utilitaire pour un commit sécurisé
    
    Returns:
        bool: True si succès, False si erreur
    
    Usage:
        ingredient = Ingredient(nom='Tomate')
        db.session.add(ingredient)
        
        if safe_commit():
            flash('Ingrédient ajouté !', 'success')
        else:
            flash('Erreur', 'danger')
    """
    try:
        db.session.commit()
        logger.debug("✅ Commit réussi")
        return True
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Commit échoué : {e}")
        return False


# ============================================
# HELPER : ROLLBACK SAFE
# ============================================

def safe_rollback():
    """
    Fonction utilitaire pour un rollback sécurisé (ne plante jamais)
    
    Usage:
        try:
            # ... opérations
        except Exception:
            safe_rollback()
    """
    try:
        db.session.rollback()
        logger.debug("🔄 Rollback effectué")
    except Exception as e:
        logger.error(f"❌ Erreur lors du rollback : {e}")


# ============================================
# CONTEXT MANAGER POUR DELETE AVEC VÉRIFICATIONS
# ============================================

@contextmanager
def db_delete_with_check(obj, check_relationships=None, success_message=None):
    """
    Context manager pour supprimer avec vérifications
    
    Args:
        obj: Objet à supprimer
        check_relationships: Liste de relations à vérifier avant suppression
        success_message: Message de succès
    
    Usage:
        ingredient = Ingredient.query.get_or_404(id)
        
        with db_delete_with_check(
            ingredient,
            check_relationships=['recettes'],
            success_message='Ingrédient supprimé'
        ):
            # La suppression se fait automatiquement si pas de relations
            pass
    
    Raises:
        ValueError: Si des relations existent
    """
    # Vérifier les relations
    if check_relationships:
        for rel_name in check_relationships:
            if hasattr(obj, rel_name):
                rel_value = getattr(obj, rel_name)
                if rel_value and len(rel_value) > 0:
                    raise ValueError(
                        f"Impossible de supprimer : {len(rel_value)} {rel_name} associé(s)"
                    )
    
    try:
        yield obj
        db.session.delete(obj)
        db.session.commit()
        
        if success_message:
            flash(success_message, 'success')
        
        logger.debug(f"✅ Suppression réussie : {obj}")
        
    except ValueError as ve:
        # Erreur de vérification de relations
        flash(str(ve), 'danger')
        raise
    
    except Exception as e:
        db.session.rollback()
        flash(f"Erreur lors de la suppression : {str(e)}", 'danger')
        logger.error(f"❌ Suppression échouée : {e}")
        raise

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
