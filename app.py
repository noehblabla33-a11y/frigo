"""
app.py
Point d'entrée de l'application Flask
"""
from flask import Flask
from flask_migrate import Migrate
from flask_compress import Compress
from models.models import db
from routes import (
    frigo_bp, recettes_bp, planification_bp, courses_bp, 
    main_bp, historique_bp, ingredients_bp, api_bp
)
from config import get_config
import os


def create_app(config_name=None):
    """
    Application Factory Pattern
    
    Args:
        config_name: 'development', 'production', 'testing' ou None
                     Si None, utilise la variable d'environnement FLASK_ENV
    
    Returns:
        Flask: Instance de l'application configurée
    """
    app = Flask(__name__)
    
    # ============================================
    # CONFIGURATION
    # ============================================
    # Charger la configuration appropriée depuis config.py
    config_class = get_config(config_name)
    app.config.from_object(config_class)
    
    # Appeler l'initialisation spécifique à l'environnement (si définie)
    if hasattr(config_class, 'init_app'):
        config_class.init_app(app)
    
    # ============================================
    # INITIALISATION DES EXTENSIONS
    # ============================================
    
    # Base de données
    db.init_app(app)
    
    # Migrations
    migrate = Migrate(app, db)

    # Compression gzip
    Compress(app)
    
    # ============================================
    # CRÉATION DES DOSSIERS NÉCESSAIRES
    # ============================================
    # Créer le dossier uploads s'il n'existe pas
    uploads_path = os.path.join(app.root_path, app.config['UPLOAD_FOLDER'])
    os.makedirs(uploads_path, exist_ok=True)
    
    # Créer le dossier logs s'il n'existe pas (pour futur logging)
    logs_path = os.path.join(app.root_path, 'logs')
    os.makedirs(logs_path, exist_ok=True)
    
    # ============================================
    # ENREGISTREMENT DES BLUEPRINTS
    # ============================================
    app.register_blueprint(main_bp)
    app.register_blueprint(ingredients_bp, url_prefix='/ingredients')
    app.register_blueprint(frigo_bp, url_prefix='/frigo')
    app.register_blueprint(recettes_bp, url_prefix='/recettes')
    app.register_blueprint(planification_bp, url_prefix='/planifier')
    app.register_blueprint(courses_bp, url_prefix='/courses')
    app.register_blueprint(historique_bp, url_prefix='/historique')
    app.register_blueprint(api_bp, url_prefix='/api/v1')
    
    # ============================================
    # CONFIGURATION DU CACHE POUR LES RESSOURCES STATIQUES
    # ============================================
    @app.after_request
    def add_cache_headers(response):
        """
        Ajoute des en-têtes de cache pour les ressources statiques
        Améliore les performances en permettant au navigateur de mettre en cache
        """
        # Ne pas mettre en cache les pages HTML
        if response.content_type.startswith('text/html'):
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
        # Mettre en cache les ressources statiques (CSS, JS, images)
        elif (response.content_type.startswith('text/css') or 
              response.content_type.startswith('application/javascript') or
              response.content_type.startswith('image/')):
            # Cache pour 1 an (31536000 secondes)
            response.headers['Cache-Control'] = f'public, max-age={app.config["SEND_FILE_MAX_AGE_DEFAULT"]}'
        
        return response
    
    # ============================================
    # CONTEXT PROCESSORS (UTILITAIRES POUR TEMPLATES)
    # ============================================
    @app.context_processor
    def utility_processor():
        """
        Ajoute des fonctions utilitaires aux templates Jinja2
        """
        def versioned_url_for(endpoint, **values):
            """
            Génère une URL avec un paramètre de version basé sur le timestamp du fichier
            Force le rechargement du cache quand un fichier change
            
            Usage dans les templates :
                {{ versioned_url_for('static', filename='style/main.css') }}
            """
            from flask import url_for
            
            if endpoint == 'static':
                filename = values.get('filename', None)
                if filename:
                    file_path = os.path.join(app.root_path, 'static', filename)
                    if os.path.exists(file_path):
                        # Utiliser le timestamp de modification du fichier
                        mtime = int(os.path.getmtime(file_path))
                        values['v'] = mtime
            
            return url_for(endpoint, **values)
        
        return dict(versioned_url_for=versioned_url_for)
    
    # ============================================
    # FILTRES JINJA2 PERSONNALISÉS
    # ============================================
    @app.template_filter('prix_lisible')
    def prix_lisible_filter(prix, unite, ingredient=None):
        """
        Affiche le prix de manière lisible
        - Si l'ingrédient a un poids_piece, affiche le prix par pièce
        - Si l'unité est 'g', convertit en €/kg pour l'affichage
        - Sinon, affiche le prix tel quel
        
        Args:
            prix: Le prix unitaire (float)
            unite: L'unité (str) - 'g', 'kg', 'ml', 'L', etc.
            ingredient: L'objet Ingredient (optionnel) pour vérifier poids_piece
        """
        if not prix or prix == 0:
            return "Prix non renseigné"
        
        # Si l'ingrédient a un poids_piece, afficher le prix par pièce
        if ingredient and hasattr(ingredient, 'poids_piece') and ingredient.poids_piece and ingredient.poids_piece > 0:
            prix_piece = prix * ingredient.poids_piece
            return f"{prix_piece:.2f}€/pièce"
        
        if unite == 'g':
            # Convertir €/g en €/kg pour l'affichage
            prix_kg = prix * 1000
            return f"{prix_kg:.2f}€/kg"
        elif unite == 'kg':
            return f"{prix:.2f}€/kg"
        elif unite == 'L':
            return f"{prix:.2f}€/L"
        elif unite == 'ml':
            prix_l = prix * 1000
            return f"{prix_l:.2f}€/L"
        else:
            return f"{prix:.2f}€/{unite}"

    @app.template_filter('quantite_lisible')
    def quantite_lisible_filter(quantite, ingredient):
        """
        Affiche la quantité de manière lisible
        - Si l'ingrédient a un poids_piece défini, convertit en pièces
        - Sinon, affiche en grammes/ml/etc
        """
        if not quantite or quantite == 0:
            return "0"
        
        # Si l'ingrédient a un poids_piece, convertir en pièces
        if ingredient and hasattr(ingredient, 'poids_piece') and ingredient.poids_piece and ingredient.poids_piece > 0:
            nb_pieces = quantite / ingredient.poids_piece
            if nb_pieces >= 1:
                return f"{nb_pieces:.1f} pièce(s)"
            else:
                # Quantité trop petite pour une pièce, afficher en grammes
                return f"{quantite:.0f} {ingredient.unite}"
        
        # Affichage normal
        return f"{quantite:.0f} {ingredient.unite}"
    
    # ============================================
    # LOGGING
    # ============================================
    if not app.debug and not app.testing:
        import logging
        from logging.handlers import RotatingFileHandler
        
        # Créer un handler pour écrire dans un fichier
        file_handler = RotatingFileHandler(
            os.path.join(logs_path, 'frigo.log'),
            maxBytes=10240000,  # 10MB
            backupCount=10
        )
        
        # Format des logs
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        
        app.logger.info('🚀 Application Frigo démarrée')
    
    return app


# ============================================
# POINT D'ENTRÉE POUR LE DÉVELOPPEMENT
# ============================================
if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000)
