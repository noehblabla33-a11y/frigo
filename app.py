from flask import Flask
from flask_migrate import Migrate
from models.models import db
from routes import frigo_bp, recettes_bp, planification_bp, courses_bp, main_bp, historique_bp, ingredients_bp, api_bp
import os

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = 'votre-clef-secrete-a-changer'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///frigo.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = 'static/uploads'
    app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB max
    
    # Créer le dossier uploads s'il n'existe pas
    os.makedirs(os.path.join(app.root_path, 'static/uploads'), exist_ok=True)
    
    # Initialiser la base de données
    db.init_app(app)
    
    # Initialiser Flask-Migrate
    migrate = Migrate(app, db)
    
    # Enregistrer les blueprints (routes)
    app.register_blueprint(main_bp)
    app.register_blueprint(ingredients_bp, url_prefix='/ingredients')
    app.register_blueprint(frigo_bp, url_prefix='/frigo')
    app.register_blueprint(recettes_bp, url_prefix='/recettes')
    app.register_blueprint(planification_bp, url_prefix='/planifier')
    app.register_blueprint(courses_bp, url_prefix='/courses')
    app.register_blueprint(historique_bp, url_prefix='/historique')
    app.register_blueprint(api_bp, url_prefix='/api/v1')

    # Configuration du cache pour les ressources statiques
    @app.after_request
    def add_cache_headers(response):
        """
        Ajoute des en-têtes de cache appropriés selon le type de ressource
        """
        # Ne pas cacher les réponses d'erreur
        if response.status_code >= 400:
            return response
        
        path = response.headers.get('X-Request-Path', '')
        
        # Images uploadées par l'utilisateur (uploads/)
        if '/static/uploads/' in path:
            # Cache long (1 an) car les noms de fichiers changent si le contenu change
            response.cache_control.public = True
            response.cache_control.max_age = 31536000  # 1 an
            response.headers['Vary'] = 'Accept-Encoding'
            
        # Images statiques, CSS, JS (static/ hors uploads)
        elif path.startswith('/static/'):
            # Distinction par type de fichier
            if any(ext in path for ext in ['.css', '.js']):
                # CSS/JS : cache moyen (1 semaine) avec validation
                response.cache_control.public = True
                response.cache_control.max_age = 604800  # 1 semaine
                response.cache_control.must_revalidate = True
                response.headers['Vary'] = 'Accept-Encoding'
                
            elif any(ext in path for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg']):
                # Images : cache long (1 mois)
                response.cache_control.public = True
                response.cache_control.max_age = 2592000  # 1 mois
                response.headers['Vary'] = 'Accept-Encoding'
                
            elif any(ext in path for ext in ['.woff', '.woff2', '.ttf', '.eot']):
                # Polices : cache très long (1 an)
                response.cache_control.public = True
                response.cache_control.max_age = 31536000  # 1 an
                response.headers['Vary'] = 'Accept-Encoding'
                
            else:
                # Autres fichiers statiques : cache court (1 jour)
                response.cache_control.public = True
                response.cache_control.max_age = 86400  # 1 jour
        
        # Pages HTML dynamiques : pas de cache ou cache très court
        elif response.content_type and 'text/html' in response.content_type:
            response.cache_control.no_cache = True
            response.cache_control.must_revalidate = True
            response.headers['Vary'] = 'Cookie'
        
        # API/JSON : pas de cache
        elif response.content_type and 'application/json' in response.content_type:
            response.cache_control.no_store = True
            response.cache_control.no_cache = True


        # Configuration CORS pour permettre les requêtes depuis android
        # Permettre les requêtes depuis n'importe quelle origine en développement
        # En production, remplacer '*' par l'origine spécifique de votre app
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,X-API-Key')
        response.headers.add('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS')
        
        return response
    
    @app.before_request
    def store_request_path():
        """
        Stocke le chemin de la requête pour l'utiliser dans after_request
        """
        from flask import request, g
        g.request_path = request.path
    
    @app.context_processor
    def utility_processor():
        """
        Ajoute des fonctions utilitaires aux templates
        """
        def versioned_url_for(endpoint, **values):
            """
            Génère une URL avec un paramètre de version basé sur le timestamp du fichier
            Utile pour forcer le rechargement du cache quand un fichier change
            """
            from flask import url_for
            import os
            
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

    @app.template_filter('prix_lisible')
    def prix_lisible_filter(prix, unite):
        """
        Affiche le prix de manière lisible
        - Si l'unité est 'g', convertit en €/kg pour l'affichage
        - Sinon, affiche le prix tel quel
        """
        if not prix or prix == 0:
            return "Prix non renseigné"
        
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
        
        # Si l'ingrédient a un poids par pièce défini
        if ingredient.poids_piece and ingredient.poids_piece > 0:
            nb_pieces = quantite / ingredient.poids_piece
            
            # Si c'est proche d'un nombre entier (±10%)
            nb_pieces_arrondi = round(nb_pieces)
            if abs(nb_pieces - nb_pieces_arrondi) / nb_pieces < 0.1:
                # Afficher en pièces en utilisant le nom de l'ingrédient
                if nb_pieces_arrondi == 1:
                    return f"1 {ingredient.nom}"
                else:
                    # Gestion du pluriel
                    nom_pluriel = pluraliser(ingredient.nom)
                    return f"{nb_pieces_arrondi} {nom_pluriel}"
            else:
                # Quantité non standard, afficher en grammes ET en pièces approximatif
                return f"{quantite:.0f}g (≈{nb_pieces:.1f} {ingredient.nom})"
        
        # Sinon, affichage normal
        if ingredient.unite == 'g':
            if quantite >= 1000:
                return f"{quantite/1000:.1f}kg"
            else:
                return f"{quantite:.0f}g"
        elif ingredient.unite == 'ml':
            if quantite >= 1000:
                return f"{quantite/1000:.1f}L"
            else:
                return f"{quantite:.0f}ml"
        else:
            return f"{quantite:.0f}{ingredient.unite}"

    def pluraliser(nom):
        """
        Gère le pluriel français de base
        """
        nom_lower = nom.lower()
        
        # Cas spéciaux
        exceptions = {
            'oeuf': 'oeufs',
            'chou': 'choux'
        }
        
        if nom_lower in exceptions:
            # Préserver la casse (majuscule initiale si nécessaire)
            resultat = exceptions[nom_lower]
            return resultat.capitalize() if nom[0].isupper() else resultat
        
        # Règles générales
        # Déjà au pluriel
        if nom_lower.endswith('s') or nom_lower.endswith('x') or nom_lower.endswith('z'):
            return nom
        
        # -au, -eau, -eu → -aux, -eaux, -eux
        if nom_lower.endswith('au') or nom_lower.endswith('eau') or nom_lower.endswith('eu'):
            return nom + 'x'
        
        # -al → -aux
        if nom_lower.endswith('al'):
            return nom[:-2] + 'aux'
        
        # Règle générale : ajouter 's'
        return nom + 's'


    return app

if __name__ == '__main__':
    app = create_app()
    app.run(
        host='0.0.0.0',  # Écoute sur toutes les interfaces
        port=5000,
        debug=True
    )

