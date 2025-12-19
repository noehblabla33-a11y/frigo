"""
app.py
Point d'entrée de l'application Flask

SYSTÈME D'UNITÉS REFACTORÉ :
Les quantités sont stockées dans l'unité native de l'ingrédient.
Les filtres Jinja2 utilisent directement l'unité sans conversion.
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
from utils.units import formater_quantite, formater_prix_unitaire
import os


def create_app(config_name=None):
    """
    Application Factory Pattern
    """
    app = Flask(__name__)
    
    # ============================================
    # CONFIGURATION
    # ============================================
    config_class = get_config(config_name)
    app.config.from_object(config_class)
    
    if hasattr(config_class, 'init_app'):
        config_class.init_app(app)
    
    # ============================================
    # INITIALISATION DES EXTENSIONS
    # ============================================
    db.init_app(app)
    migrate = Migrate(app, db)
    Compress(app)
    
    # ============================================
    # CRÉATION DES DOSSIERS NÉCESSAIRES
    # ============================================
    uploads_path = os.path.join(app.root_path, app.config['UPLOAD_FOLDER'])
    os.makedirs(uploads_path, exist_ok=True)
    
    logs_path = os.path.join(app.root_path, 'logs')
    os.makedirs(logs_path, exist_ok=True)
    
    # ============================================
    # ENREGISTREMENT DES BLUEPRINTS
    # ============================================
    app.register_blueprint(main_bp)
    app.register_blueprint(frigo_bp, url_prefix='/frigo')
    app.register_blueprint(recettes_bp, url_prefix='/recettes')
    app.register_blueprint(planification_bp, url_prefix='/planification')
    app.register_blueprint(courses_bp, url_prefix='/courses')
    app.register_blueprint(historique_bp, url_prefix='/historique')
    app.register_blueprint(ingredients_bp, url_prefix='/ingredients')
    app.register_blueprint(api_bp, url_prefix='/api')

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
            """
            from flask import url_for
            
            if endpoint == 'static':
                filename = values.get('filename', None)
                if filename:
                    file_path = os.path.join(app.root_path, 'static', filename)
                    if os.path.exists(file_path):
                        mtime = int(os.path.getmtime(file_path))
                        values['v'] = mtime
            
            return url_for(endpoint, **values)
        
        return dict(versioned_url_for=versioned_url_for)
    
    # ============================================
    # FILTRES JINJA2 PERSONNALISÉS - SIMPLIFIÉS
    # ============================================
    
    @app.template_filter('quantite_lisible')
    def quantite_lisible_filter(quantite, ingredient):
        """
        Affiche la quantité de manière lisible.
        
        NOUVEAU SYSTÈME : La quantité est déjà dans l'unité native de l'ingrédient.
        - 2 œufs → "2 œufs"
        - 500g de farine → "500g"
        - 250ml de lait → "250ml"
        
        Args:
            quantite: Quantité dans l'unité native
            ingredient: Objet Ingredient
        
        Returns:
            String formatée pour l'affichage
        """
        return formater_quantite(quantite, ingredient)
    
    @app.template_filter('prix_lisible')
    def prix_lisible_filter(prix, unite, ingredient=None):
        """
        Affiche le prix de manière lisible.
        
        Le prix_unitaire est stocké par unité native :
        - €/pièce pour les pièces
        - €/g pour les grammes (affiché en €/kg)
        - €/ml pour les millilitres (affiché en €/L)
        
        Args:
            prix: Le prix unitaire
            unite: L'unité (peut être ignoré si ingredient est fourni)
            ingredient: L'objet Ingredient (optionnel)
        """
        if ingredient:
            return formater_prix_unitaire(ingredient)
        
        # Fallback si pas d'ingrédient
        if not prix or prix == 0:
            return "Prix non renseigné"
        
        if unite == 'pièce':
            return f"{prix:.2f}€/pièce"
        elif unite == 'g':
            prix_kg = prix * 1000
            return f"{prix_kg:.2f}€/kg"
        elif unite == 'ml':
            prix_l = prix * 1000
            return f"{prix_l:.2f}€/L"
        else:
            return f"{prix:.2f}€/{unite}"

    @app.template_filter('format_unite')
    def format_unite_filter(unite, quantite=1):
        """
        Formate l'unité pour l'affichage.
        
        Args:
            unite: L'unité de base
            quantite: Quantité pour gérer le pluriel
        """
        if unite == 'pièce':
            return 'pièce(s)' if quantite > 1 else 'pièce'
        return unite

    # ============================================
    # LOGGING
    # ============================================
    if not app.debug and not app.testing:
        import logging
        from logging.handlers import RotatingFileHandler
        
        file_handler = RotatingFileHandler(
            os.path.join(logs_path, 'frigo.log'),
            maxBytes=10240000,
            backupCount=10
        )
        
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
