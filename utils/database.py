from contextlib import contextmanager
from functools import wraps
from flask import flash, current_app
from sqlalchemy import func
from models.models import db
import logging

logger = logging.getLogger(__name__)


@contextmanager
def db_transaction():
    """
    Context manager pour gérer automatiquement les transactions.

    Commit si aucune erreur, rollback sinon. Re-lève l'exception pour
    que l'appelant puisse la gérer.
    """
    try:
        yield db.session
        db.session.commit()
        logger.debug("Transaction committée avec succès")
    except Exception as e:
        db.session.rollback()
        logger.error(f"Transaction annulée : {e}")
        raise


@contextmanager
def db_transaction_with_flash(success_message=None, error_message=None):
    """
    Context manager avec gestion automatique des messages flash.

    Args:
        success_message: Message en cas de succès (None = pas de message)
        error_message: Message en cas d'erreur (None = message par défaut)
    """
    try:
        yield db.session
        db.session.commit()

        if success_message:
            flash(success_message, 'success')

        logger.debug(f"Transaction réussie : {success_message or 'OK'}")

    except Exception as e:
        db.session.rollback()

        error_msg = error_message or f"Une erreur est survenue : {str(e)}"
        flash(error_msg, 'danger')

        logger.error(f"Transaction échouée : {e}")
        raise


@contextmanager
def db_transaction_with_retry(max_retries=3, success_message=None):
    """
    Context manager avec système de retry automatique.

    Args:
        max_retries: Nombre maximum de tentatives
        success_message: Message de succès (optionnel)
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

            logger.debug(f"Transaction réussie (tentative {attempt + 1}/{max_retries})")
            return

        except (OperationalError, IntegrityError) as e:
            db.session.rollback()
            last_exception = e

            logger.warning(f"Tentative {attempt + 1}/{max_retries} échouée : {e}")

            if attempt < max_retries - 1:
                time.sleep(0.1 * (attempt + 1))
            else:
                flash(f"Erreur après {max_retries} tentatives", 'danger')
                raise last_exception

        except Exception as e:
            db.session.rollback()
            logger.error(f"Erreur non-récupérable : {e}")
            flash(f"Erreur : {str(e)}", 'danger')
            raise


def with_db_transaction(success_message=None, error_message=None):
    """
    Décorateur pour entourer une route d'une transaction automatique.

    Args:
        success_message: Message de succès (optionnel)
        error_message: Message d'erreur (optionnel)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                db.session.commit()

                if success_message:
                    flash(success_message, 'success')

                logger.debug(f"Transaction de {func.__name__} réussie")
                return result

            except Exception as e:
                db.session.rollback()

                error_msg = error_message or f"Erreur dans {func.__name__}: {str(e)}"
                flash(error_msg, 'danger')

                logger.error(f"Transaction de {func.__name__} échouée : {e}")
                raise

        return wrapper
    return decorator


def safe_commit():
    """
    Effectue un commit sécurisé.

    Returns:
        True si succès, False si erreur
    """
    try:
        db.session.commit()
        logger.debug("Commit réussi")
        return True
    except Exception as e:
        db.session.rollback()
        logger.error(f"Commit échoué : {e}")
        return False


def safe_rollback():
    """
    Effectue un rollback sécurisé (ne lève jamais d'exception).
    """
    try:
        db.session.rollback()
        logger.debug("Rollback effectué")
    except Exception as e:
        logger.error(f"Erreur lors du rollback : {e}")


@contextmanager
def db_delete_with_check(obj, check_relationships=None, success_message=None):
    """
    Context manager pour supprimer un objet avec vérifications préalables.

    Args:
        obj: Objet à supprimer
        check_relationships: Liste de relations à vérifier avant suppression
        success_message: Message de succès
    """
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

        logger.debug(f"Suppression réussie : {obj}")

    except ValueError as ve:
        flash(str(ve), 'danger')
        raise

    except Exception as e:
        db.session.rollback()
        flash(f"Erreur lors de la suppression : {str(e)}", 'danger')
        logger.error(f"Suppression échouée : {e}")
        raise

def paginate_query(query, page, per_page=None):
    """
    Pagine une requête SQLAlchemy.

    Args:
        query: Requête SQLAlchemy à paginer
        page: Numéro de page (commence à 1)
        per_page: Nombre d'items par page (None = valeur depuis la config)

    Returns:
        Dict avec items, total, page, pages, per_page, has_prev, has_next, prev_page, next_page
    """
    if per_page is None:
        per_page = current_app.config.get('ITEMS_PER_PAGE_DEFAULT', 24)

    per_page = max(1, per_page)
    page = max(1, page)

    total = db.session.query(func.count()).select_from(query.subquery()).scalar()

    if total > 0:
        pages = (total + per_page - 1) // per_page
    else:
        pages = 1

    page = min(page, pages)

    offset = (page - 1) * per_page
    items = query.limit(per_page).offset(offset).all()

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

    Utile quand le filtrage doit se faire en Python après la requête DB.

    Args:
        items: Liste d'éléments à paginer
        page: Numéro de page (1-indexed)
        per_page: Nombre d'éléments par page

    Returns:
        Dict de pagination compatible avec les templates
    """
    total = len(items)
    pages = (total + per_page - 1) // per_page if total > 0 else 1

    page = min(max(1, page), pages)

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
