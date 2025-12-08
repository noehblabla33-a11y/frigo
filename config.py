"""
config.py
Configuration technique de l'application Flask
Contient les paramètres liés à l'infrastructure : base de données, sécurité, uploads, etc.
"""
import os


class Config:
    """Configuration de base commune à tous les environnements"""
    
    # ============================================
    # SÉCURITÉ
    # ============================================
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'votre-clef-secrete-a-changer'
    
    # ============================================
    # BASE DE DONNÉES
    # ============================================
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///frigo.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False  # Afficher les requêtes SQL en développement
    
    # ============================================
    # UPLOAD DE FICHIERS
    # ============================================
    UPLOAD_FOLDER = 'static/uploads'
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5MB max
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    
    # ============================================
    # PAGINATION
    # ============================================
    ITEMS_PER_PAGE_DEFAULT = 24
    ITEMS_PER_PAGE_RECETTES = 20  # Pagination spécifique pour les recettes
    
    # ============================================
    # API / AUTHENTIFICATION
    # ============================================
    API_KEY = os.environ.get('API_KEY') or 'ma_clef'
    
    # ⚠️ IMPORTANT : En production, définir ces variables d'environnement :
    # export SECRET_KEY="votre-vraie-clef-secrete-complexe"
    # export API_KEY="votre-vraie-clef-api-complexe"
    # export DATABASE_URL="postgresql://user:pass@host/dbname"  # Pour PostgreSQL en prod
    
    # ============================================
    # CACHE / PERFORMANCE
    # ============================================
    SEND_FILE_MAX_AGE_DEFAULT = 31536000  # 1 an pour les fichiers statiques


class DevelopmentConfig(Config):
    """Configuration pour le développement local"""
    DEBUG = True
    TESTING = False
    SQLALCHEMY_ECHO = True  # Afficher les requêtes SQL en développement


class ProductionConfig(Config):
    """Configuration pour la production"""
    DEBUG = False
    TESTING = False
    SQLALCHEMY_ECHO = False
    
    # En production, forcer l'utilisation de variables d'environnement sécurisées
    def __init__(self):
        super().__init__()
        
        # Vérifier que les secrets sont définis en production
        if not os.environ.get('SECRET_KEY'):
            raise ValueError(
                "⚠️ ERREUR CRITIQUE : SECRET_KEY doit être définie en production!\n"
                "Définissez-la avec: export SECRET_KEY='votre-clef-secrete-complexe'"
            )
        
        if not os.environ.get('API_KEY'):
            raise ValueError(
                "⚠️ ERREUR CRITIQUE : API_KEY doit être définie en production!\n"
                "Définissez-la avec: export API_KEY='votre-clef-api-complexe'"
            )


class TestingConfig(Config):
    """Configuration pour les tests unitaires"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'  # Base de données en mémoire
    WTF_CSRF_ENABLED = False  # Désactiver CSRF pour les tests
    SQLALCHEMY_ECHO = False


# Dictionnaire pour faciliter la sélection de la configuration
config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config(config_name=None):
    """
    Récupère la configuration appropriée
    
    Args:
        config_name: 'development', 'production', 'testing' ou None (utilise FLASK_ENV)
    
    Returns:
        Classe de configuration appropriée
    """
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    return config_by_name.get(config_name, DevelopmentConfig)
