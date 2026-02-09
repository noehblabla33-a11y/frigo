"""
app.py
Point d'entrée de l'application Flask

SYSTÈME D'UNITÉS REFACTORÉ :
Les quantités sont stockées dans l'unité native de l'ingrédient.
Les filtres Jinja2 utilisent directement l'unité sans conversion.

✅ NOUVEAU : Contexte des saisons pour tous les templates
"""
from flask import Flask, url_for
from flask_migrate import Migrate
from flask_compress import Compress
from models.models import db
from routes import (
    frigo_bp, recettes_bp, planification_bp, courses_bp, 
    main_bp, historique_bp, ingredients_bp, api_bp, recommandations_bp
)
from config import get_config
from utils.calculs import formater_quantite, formater_prix_unitaire
from utils.saisons import get_saison_actuelle, get_contexte_saison, formater_saison, formater_liste_saisons
from utils.cache import cache, init_cache
from utils.errors import init_error_handlers
from constants import SAISONS_EMOJIS, SAISONS_NOMS
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
    Migrate(app, db)
    init_cache(app)
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
    app.register_blueprint(api_bp, url_prefix='/api/v1')
    app.register_blueprint(recommandations_bp, url_prefix='/recommandations')
    
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
            if endpoint == 'static':
                filename = values.get('filename', None)
                if filename:
                    file_path = os.path.join(app.root_path, 'static', filename)
                    if os.path.exists(file_path):
                        mtime = int(os.path.getmtime(file_path))
                        values['v'] = mtime
            
            return url_for(endpoint, **values)
        
        return {
            'versioned_url_for': versioned_url_for,
            # Formatage des quantités et prix
            'formater_quantite': formater_quantite,
            'formater_prix_unitaire': formater_prix_unitaire,
            
            # ✅ NOUVEAU : Fonctions pour les saisons
            'get_saison_actuelle': get_saison_actuelle,
            'formater_saison': formater_saison,
            'formater_liste_saisons': formater_liste_saisons,
            'saisons_emojis': SAISONS_EMOJIS,
            'saisons_noms': SAISONS_NOMS,
        }
    
    @app.context_processor
    def inject_saison_context():
        """
        ✅ NOUVEAU : Injecte le contexte de saison dans tous les templates.
        Cela permet d'afficher la saison actuelle partout si nécessaire.
        """
        return get_contexte_saison()

    # ============================================
    # FILTRES JINJA2 PERSONNALISÉS
    # ============================================
    
    @app.template_filter('quantite_lisible')
    def quantite_lisible_filter(quantite, ingredient):
        """
        Affiche la quantité de manière lisible.
        """
        return formater_quantite(quantite, ingredient)
    
    @app.template_filter('prix_lisible')
    def prix_lisible_filter(prix, unite, ingredient=None):
        """
        Affiche le prix de manière lisible.
        """
        if ingredient:
            return formater_prix_unitaire(ingredient)
        
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
        """
        if unite == 'pièce':
            return 'pièce' if quantite <= 1 else 'pièces'
        return unite

    @app.template_filter('image_path')
    def image_path_filter(path):
        """
        Normalise le chemin d'une image pour url_for('static', ...).
        
        Les images sont stockées en DB avec le préfixe 'static/' 
        (ex: 'static/uploads/image.jpg'), mais url_for('static', filename=...)
        attend un chemin relatif au dossier static (ex: 'uploads/image.jpg').
        
        Usage dans les templates :
            {{ url_for('static', filename=obj.image|image_path) }}
        """
        if not path:
            return ''
        if path.startswith('static/'):
            return path[7:]  # len('static/') = 7
        return path

    return app

# Point d'entrée pour le développement
if __name__ == '__main__':
    app = create_app()
    init_error_handlers(app)
    app.run(host='0.0.0.0', port=5000)
