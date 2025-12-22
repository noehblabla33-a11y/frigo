"""
utils/routes.py
Décorateurs et utilitaires pour les routes Flask

Ce module fournit :
- Décorateurs pour simplifier les routes CRUD
- Helpers pour les redirections et messages
- Gestionnaires de formulaires réutilisables
"""
from functools import wraps
from flask import request, redirect, url_for, flash, render_template, current_app
from models.models import db


# ============================================
# DÉCORATEURS POUR ROUTES
# ============================================

def handle_form_errors(redirect_endpoint):
    """
    Décorateur pour gérer les erreurs de formulaire de manière uniforme.
    
    En cas d'exception, effectue un rollback et redirige avec un message d'erreur.
    
    Usage:
        @app.route('/create', methods=['POST'])
        @handle_form_errors('items.liste')
        def create():
            # code qui peut lever une exception
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except ValueError as e:
                # Erreur de validation
                flash(str(e), 'danger')
                db.session.rollback()
            except Exception as e:
                # Erreur inattendue
                current_app.logger.error(f'Erreur dans {f.__name__}: {str(e)}')
                flash(f'Une erreur est survenue : {str(e)}', 'danger')
                db.session.rollback()
            
            return redirect(url_for(redirect_endpoint))
        return decorated_function
    return decorator


def require_post(f):
    """
    Décorateur qui s'assure que la requête est POST.
    Sinon, redirige vers la page précédente.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method != 'POST':
            return redirect(request.referrer or url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function


def with_item(model, param_name='id', redirect_on_404='main.index'):
    """
    Décorateur qui charge un item de la base de données.
    
    Usage:
        @app.route('/item/<int:id>')
        @with_item(Ingredient)
        def show(item):
            return render_template('item.html', ingredient=item)
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            item_id = kwargs.get(param_name)
            if item_id is None:
                flash('ID invalide.', 'danger')
                return redirect(url_for(redirect_on_404))
            
            item = model.query.get(item_id)
            if item is None:
                flash('Élément non trouvé.', 'danger')
                return redirect(url_for(redirect_on_404))
            
            # Remplacer l'ID par l'item dans kwargs
            kwargs['item'] = item
            del kwargs[param_name]
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# ============================================
# HELPERS DE REDIRECTION
# ============================================

def redirect_back(default_endpoint='main.index', **kwargs):
    """
    Redirige vers la page précédente ou vers un endpoint par défaut.
    
    Cherche dans l'ordre :
    1. Le paramètre 'next' dans le formulaire
    2. Le referrer HTTP
    3. L'endpoint par défaut
    
    Usage:
        return redirect_back('items.liste')
    """
    next_url = request.form.get('next') or request.referrer
    if next_url:
        return redirect(next_url)
    return redirect(url_for(default_endpoint, **kwargs))


def flash_and_redirect(message, category, endpoint, **kwargs):
    """
    Affiche un message flash et redirige.
    
    Usage:
        return flash_and_redirect('Item créé !', 'success', 'items.liste')
    """
    flash(message, category)
    return redirect(url_for(endpoint, **kwargs))


def success_redirect(message, endpoint, **kwargs):
    """Raccourci pour flash_and_redirect avec category='success'"""
    return flash_and_redirect(message, 'success', endpoint, **kwargs)


def error_redirect(message, endpoint, **kwargs):
    """Raccourci pour flash_and_redirect avec category='danger'"""
    return flash_and_redirect(message, 'danger', endpoint, **kwargs)


# ============================================
# HELPERS DE FORMULAIRES
# ============================================

class FormHelper:
    """
    Classe utilitaire pour traiter les formulaires de manière uniforme.
    
    Usage:
        helper = FormHelper(request.form)
        nom = helper.get_string('nom', required=True)
        prix = helper.get_float('prix', default=0)
        categorie = helper.get_string('categorie', allow_empty=True)
    """
    
    def __init__(self, form_data):
        self.form = form_data
        self.errors = []
    
    def get_string(self, name, default='', required=False, allow_empty=False, strip=True):
        """
        Récupère une valeur string du formulaire.
        
        Args:
            name: Nom du champ
            default: Valeur par défaut
            required: Si True, lève une erreur si vide
            allow_empty: Si True, retourne None pour les valeurs vides
            strip: Si True, supprime les espaces
        """
        value = self.form.get(name, default)
        
        if strip and value:
            value = value.strip()
        
        if not value:
            if required:
                self.errors.append(f'Le champ "{name}" est requis.')
                return default
            if allow_empty:
                return None
            return default
        
        return value
    
    def get_float(self, name, default=0.0, required=False, min_val=None, max_val=None):
        """
        Récupère une valeur float du formulaire.
        """
        value = self.form.get(name, '')
        
        if not value:
            if required:
                self.errors.append(f'Le champ "{name}" est requis.')
            return default
        
        try:
            result = float(value)
            
            if min_val is not None and result < min_val:
                self.errors.append(f'Le champ "{name}" doit être >= {min_val}.')
                return default
            
            if max_val is not None and result > max_val:
                self.errors.append(f'Le champ "{name}" doit être <= {max_val}.')
                return default
            
            return result
        except (ValueError, TypeError):
            if required:
                self.errors.append(f'Le champ "{name}" doit être un nombre.')
            return default
    
    def get_int(self, name, default=0, required=False, min_val=None, max_val=None):
        """
        Récupère une valeur int du formulaire.
        """
        value = self.get_float(name, default=float(default), required=required, 
                               min_val=min_val, max_val=max_val)
        return int(value) if value is not None else default
    
    def get_bool(self, name, default=False):
        """
        Récupère une valeur boolean du formulaire (checkbox).
        """
        value = self.form.get(name, '')
        return value.lower() in ('true', '1', 'on', 'yes', 'oui')
    
    def get_list(self, prefix, fields, max_items=100):
        """
        Récupère une liste d'items du formulaire.
        
        Usage:
            items = helper.get_list('ingredient', ['id', 'quantite'])
            # Cherche ingredient_0_id, ingredient_0_quantite, etc.
        
        Args:
            prefix: Préfixe des champs
            fields: Liste des noms de champs
            max_items: Nombre maximum d'items
        
        Returns:
            Liste de dictionnaires
        """
        items = []
        
        for i in range(max_items):
            item = {}
            has_value = False
            
            for field in fields:
                key = f'{prefix}_{i}' if field == 'main' else f'{prefix}_{i}_{field}'
                # Support aussi le format field_i (sans underscore au milieu)
                if key not in self.form:
                    key = f'{field}_{i}'
                
                value = self.form.get(key, '')
                item[field] = value
                if value:
                    has_value = True
            
            if has_value:
                items.append(item)
            else:
                # Fin de la liste si aucune valeur trouvée
                break
        
        return items
    
    def has_errors(self):
        """Retourne True s'il y a des erreurs de validation."""
        return len(self.errors) > 0
    
    def get_errors(self):
        """Retourne la liste des erreurs."""
        return self.errors
    
    def flash_errors(self):
        """Affiche toutes les erreurs comme messages flash."""
        for error in self.errors:
            flash(error, 'danger')
    
    def validate(self):
        """
        Valide le formulaire. Lève ValueError si invalide.
        """
        if self.has_errors():
            raise ValueError('; '.join(self.errors))
        return True


# ============================================
# GESTIONNAIRE DE PAGINATION
# ============================================

def get_pagination_args(default_page=1, default_per_page=20):
    """
    Récupère les arguments de pagination depuis la requête.
    
    Returns:
        Tuple (page, per_page)
    """
    try:
        page = int(request.args.get('page', default_page))
        if page < 1:
            page = default_page
    except (ValueError, TypeError):
        page = default_page
    
    try:
        per_page = int(request.args.get('per_page', default_per_page))
        if per_page < 1 or per_page > 100:
            per_page = default_per_page
    except (ValueError, TypeError):
        per_page = default_per_page
    
    return page, per_page


def get_search_args(*field_names):
    """
    Récupère les arguments de recherche depuis la requête.
    
    Usage:
        search, categorie, type = get_search_args('search', 'categorie', 'type')
    
    Returns:
        Tuple des valeurs (vides si non présentes)
    """
    return tuple(request.args.get(name, '') for name in field_names)


# ============================================
# CONTEXT PROCESSORS
# ============================================

def register_route_helpers(app):
    """
    Enregistre des fonctions utilitaires dans le contexte Jinja2.
    
    Usage dans app.py:
        from utils.routes import register_route_helpers
        register_route_helpers(app)
    
    Disponible dans les templates:
        {{ is_active('ingredients.liste') }}
    """
    
    @app.context_processor
    def route_utilities():
        def is_active(endpoint, **kwargs):
            """Vérifie si l'endpoint donné est la page actuelle."""
            return request.endpoint == endpoint
        
        def is_active_blueprint(blueprint_name):
            """Vérifie si le blueprint donné est actif."""
            return request.blueprint == blueprint_name
        
        return {
            'is_active': is_active,
            'is_active_blueprint': is_active_blueprint
        }
