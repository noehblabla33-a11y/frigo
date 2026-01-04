"""
utils/errors.py
Gestion centralisée des erreurs pour l'application

✅ OPTIMISATION TECHNIQUE - Gestion d'erreurs centralisée
- Error handlers globaux pour toutes les erreurs HTTP
- Logging structuré des erreurs
- Pages d'erreur personnalisées
- Helpers pour les erreurs métier

INSTALLATION:
    1. Copier ce fichier dans utils/
    2. Créer les templates d'erreur dans templates/errors/
    3. Appeler init_error_handlers(app) dans create_app()

USAGE:
    from utils.errors import (
        init_error_handlers,
        AppError,
        ValidationError,
        NotFoundError
    )
"""
import traceback
from functools import wraps
from flask import render_template, jsonify, request, current_app, flash, redirect, url_for
from werkzeug.exceptions import HTTPException


# ============================================
# EXCEPTIONS PERSONNALISÉES
# ============================================

class AppError(Exception):
    """
    Exception de base pour les erreurs de l'application.
    
    Usage:
        raise AppError("Message d'erreur", code=400)
    """
    def __init__(self, message, code=500, payload=None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.payload = payload
    
    def to_dict(self):
        return {
            'success': False,
            'error': self.message,
            'code': self.code,
            'payload': self.payload
        }


class ValidationError(AppError):
    """Erreur de validation des données."""
    def __init__(self, message, field=None):
        super().__init__(message, code=400)
        self.field = field
        self.payload = {'field': field} if field else None


class NotFoundError(AppError):
    """Ressource non trouvée."""
    def __init__(self, resource_type='Ressource', resource_id=None):
        message = f"{resource_type} non trouvé(e)"
        if resource_id:
            message += f" (ID: {resource_id})"
        super().__init__(message, code=404)


class PermissionError(AppError):
    """Erreur de permission."""
    def __init__(self, message="Accès non autorisé"):
        super().__init__(message, code=403)


class ConflictError(AppError):
    """Conflit de données (ex: doublon)."""
    def __init__(self, message="Conflit de données"):
        super().__init__(message, code=409)


class DatabaseError(AppError):
    """Erreur de base de données."""
    def __init__(self, message="Erreur de base de données", original_error=None):
        super().__init__(message, code=500)
        self.original_error = original_error


# ============================================
# HELPERS POUR LE LOGGING
# ============================================

def log_error(error, include_traceback=True):
    """
    Log une erreur de manière structurée.
    
    Args:
        error: L'exception à logger
        include_traceback: Inclure la stack trace
    """
    error_info = {
        'type': type(error).__name__,
        'message': str(error),
        'url': request.url if request else 'N/A',
        'method': request.method if request else 'N/A',
        'ip': request.remote_addr if request else 'N/A',
    }
    
    # Ajouter les infos de la requête
    if request:
        error_info['user_agent'] = request.user_agent.string
        if request.form:
            # Ne pas logger les mots de passe !
            safe_form = {k: v for k, v in request.form.items() 
                        if 'password' not in k.lower() and 'secret' not in k.lower()}
            error_info['form_data'] = safe_form
    
    # Logger
    log_message = f"[{error_info['type']}] {error_info['message']}"
    log_message += f" | URL: {error_info['url']} | Method: {error_info['method']}"
    
    current_app.logger.error(log_message)
    
    if include_traceback:
        current_app.logger.error(traceback.format_exc())
    
    return error_info


def is_api_request():
    """Détermine si la requête attend une réponse JSON."""
    if request.path.startswith('/api/'):
        return True
    if request.accept_mimetypes.best == 'application/json':
        return True
    if request.is_json:
        return True
    return False


# ============================================
# ERROR HANDLERS
# ============================================

def handle_400(error):
    """Bad Request - Requête invalide."""
    log_error(error, include_traceback=False)
    
    if is_api_request():
        return jsonify({
            'success': False,
            'error': 'Requête invalide',
            'message': str(error.description) if hasattr(error, 'description') else str(error)
        }), 400
    
    return render_template('errors/400.html', error=error), 400


def handle_403(error):
    """Forbidden - Accès interdit."""
    log_error(error, include_traceback=False)
    
    if is_api_request():
        return jsonify({
            'success': False,
            'error': 'Accès interdit',
            'message': 'Vous n\'avez pas les permissions nécessaires.'
        }), 403
    
    return render_template('errors/403.html', error=error), 403


def handle_404(error):
    """Not Found - Page non trouvée."""
    # Ne pas logger les 404 en détail (trop de bruit)
    current_app.logger.info(f"404: {request.url}")
    
    if is_api_request():
        return jsonify({
            'success': False,
            'error': 'Ressource non trouvée',
            'path': request.path
        }), 404
    
    return render_template('errors/404.html', error=error), 404


def handle_405(error):
    """Method Not Allowed."""
    log_error(error, include_traceback=False)
    
    if is_api_request():
        return jsonify({
            'success': False,
            'error': 'Méthode non autorisée',
            'method': request.method,
            'allowed': error.valid_methods if hasattr(error, 'valid_methods') else []
        }), 405
    
    return render_template('errors/405.html', error=error), 405


def handle_500(error):
    """Internal Server Error."""
    log_error(error, include_traceback=True)
    
    if is_api_request():
        return jsonify({
            'success': False,
            'error': 'Erreur interne du serveur',
            'message': 'Une erreur inattendue s\'est produite.'
        }), 500
    
    return render_template('errors/500.html', error=error), 500


def handle_app_error(error):
    """Handler pour les AppError personnalisées."""
    log_error(error, include_traceback=False)
    
    if is_api_request():
        return jsonify(error.to_dict()), error.code
    
    # Pour les erreurs web, flash et redirect
    flash(error.message, 'danger')
    return redirect(request.referrer or url_for('main.index'))


def handle_generic_exception(error):
    """Handler pour toutes les exceptions non gérées."""
    log_error(error, include_traceback=True)
    
    # En développement, laisser l'erreur remonter pour le debugger
    if current_app.debug:
        raise error
    
    if is_api_request():
        return jsonify({
            'success': False,
            'error': 'Erreur interne',
            'message': 'Une erreur inattendue s\'est produite.'
        }), 500
    
    return render_template('errors/500.html', error=error), 500


# ============================================
# INITIALISATION
# ============================================

def init_error_handlers(app):
    """
    Initialise tous les error handlers pour l'application.
    
    À appeler dans create_app() :
        from utils.errors import init_error_handlers
        init_error_handlers(app)
    
    Args:
        app: Instance Flask
    """
    # Erreurs HTTP standard
    app.register_error_handler(400, handle_400)
    app.register_error_handler(403, handle_403)
    app.register_error_handler(404, handle_404)
    app.register_error_handler(405, handle_405)
    app.register_error_handler(500, handle_500)
    
    # Erreurs personnalisées
    app.register_error_handler(AppError, handle_app_error)
    app.register_error_handler(ValidationError, handle_app_error)
    app.register_error_handler(NotFoundError, handle_app_error)
    
    # Toutes les autres exceptions
    app.register_error_handler(Exception, handle_generic_exception)
    
    app.logger.info('✅ Error handlers initialisés')


# ============================================
# DÉCORATEURS UTILES
# ============================================

def handle_errors(flash_message=None, redirect_to=None):
    """
    Décorateur pour gérer automatiquement les erreurs dans une route.
    
    Usage:
        @app.route('/ma-route')
        @handle_errors(flash_message="Erreur lors de l'opération", redirect_to='main.index')
        def ma_route():
            # Code qui peut lever des exceptions
            ...
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except AppError as e:
                flash(e.message, 'danger')
                if redirect_to:
                    return redirect(url_for(redirect_to))
                return redirect(request.referrer or url_for('main.index'))
            except Exception as e:
                log_error(e)
                message = flash_message or "Une erreur s'est produite."
                flash(message, 'danger')
                if redirect_to:
                    return redirect(url_for(redirect_to))
                return redirect(request.referrer or url_for('main.index'))
        return wrapper
    return decorator


def api_error_handler(f):
    """
    Décorateur pour les routes API avec gestion d'erreurs standardisée.
    
    Usage:
        @api_bp.route('/endpoint')
        @api_error_handler
        def mon_endpoint():
            # Code...
            return jsonify({'success': True, 'data': data})
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except AppError as e:
            return jsonify(e.to_dict()), e.code
        except HTTPException as e:
            return jsonify({
                'success': False,
                'error': e.name,
                'message': e.description
            }), e.code
        except Exception as e:
            log_error(e)
            return jsonify({
                'success': False,
                'error': 'Erreur interne',
                'message': str(e) if current_app.debug else 'Une erreur s\'est produite.'
            }), 500
    return wrapper


# ============================================
# VALIDATEURS AVEC ERREURS CLAIRES
# ============================================

def require_fields(data, fields):
    """
    Vérifie que les champs requis sont présents.
    
    Args:
        data: Dict de données
        fields: Liste de noms de champs requis
    
    Raises:
        ValidationError si un champ manque
    """
    missing = [f for f in fields if not data.get(f)]
    if missing:
        raise ValidationError(
            f"Champ(s) requis manquant(s): {', '.join(missing)}",
            field=missing[0]
        )


def validate_positive_number(value, field_name):
    """
    Valide qu'une valeur est un nombre positif.
    
    Args:
        value: Valeur à valider
        field_name: Nom du champ pour le message d'erreur
    
    Returns:
        float: La valeur convertie
    
    Raises:
        ValidationError si invalide
    """
    try:
        num = float(value)
        if num < 0:
            raise ValidationError(f"{field_name} doit être positif", field=field_name)
        return num
    except (TypeError, ValueError):
        raise ValidationError(f"{field_name} doit être un nombre", field=field_name)


def validate_in_list(value, allowed_values, field_name):
    """
    Valide qu'une valeur est dans une liste autorisée.
    
    Args:
        value: Valeur à valider
        allowed_values: Liste des valeurs autorisées
        field_name: Nom du champ
    
    Raises:
        ValidationError si valeur non autorisée
    """
    if value and value not in allowed_values:
        raise ValidationError(
            f"{field_name} invalide. Valeurs autorisées: {', '.join(map(str, allowed_values))}",
            field=field_name
        )
