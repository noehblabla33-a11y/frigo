from flask import Flask
from flask_migrate import Migrate
from models.models import db
from routes import frigo_bp, recettes_bp, planification_bp, courses_bp, main_bp, historique_bp, ingredients_bp
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
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)


## Optimisation cache pour images
@app.after_request
def add_header(response):
    if 'static/' in response.headers.get('Content-Type', ''):
        response.cache_control.max_age = 31536000
    return response
