"""
Middleware pour gérer le cache de manière plus avancée
"""
from flask import request, make_response
from functools import wraps
import hashlib

def add_cache_control(max_age=3600, public=True, must_revalidate=False):
    """
    Décorateur pour ajouter des en-têtes de cache à une route spécifique
    
    Usage:
    @app.route('/ma-page')
    @add_cache_control(max_age=86400, public=True)
    def ma_page():
        return render_template('ma_page.html')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            response = make_response(f(*args, **kwargs))
            
            if public:
                response.cache_control.public = True
            else:
                response.cache_control.private = True
            
            response.cache_control.max_age = max_age
            
            if must_revalidate:
                response.cache_control.must_revalidate = True
            
            return response
        return decorated_function
    return decorator

def generate_etag(data):
    """
    Génère un ETag basé sur le contenu
    Utile pour les réponses dynamiques qui peuvent être mises en cache
    """
    if isinstance(data, str):
        data = data.encode('utf-8')
    return hashlib.md5(data).hexdigest()

def conditional_response(response_data, etag=None):
    """
    Gère les requêtes conditionnelles (If-None-Match)
    Retourne 304 Not Modified si le contenu n'a pas changé
    
    Usage:
    @app.route('/api/data')
    def get_data():
        data = get_my_data()
        etag = generate_etag(str(data))
        return conditional_response(jsonify(data), etag=etag)
    """
    if etag is None:
        etag = generate_etag(str(response_data))
    
    # Vérifier si le client a déjà cette version
    if request.headers.get('If-None-Match') == etag:
        response = make_response('', 304)
    else:
        response = make_response(response_data)
    
    response.headers['ETag'] = etag
    return response

def no_cache():
    """
    Décorateur pour désactiver complètement le cache
    Utile pour les pages avec des données sensibles ou très dynamiques
    
    Usage:
    @app.route('/admin')
    @no_cache()
    def admin():
        return render_template('admin.html')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            response = make_response(f(*args, **kwargs))
            response.cache_control.no_store = True
            response.cache_control.no_cache = True
            response.cache_control.must_revalidate = True
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
            return response
        return decorated_function
    return decorator
