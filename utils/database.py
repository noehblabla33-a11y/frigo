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
