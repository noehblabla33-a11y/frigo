"""
config.py
Configuration technique de l'application Flask
Contient les paramètres liés à l'infrastructure : base de données, sécurité, uploads, etc.

✅ VERSION OPTIMISÉE - PHASE 1
- Charge les variables depuis .env
- Fallback sur valeurs par défaut en dev
- Validation stricte en production
"""
import os
from dotenv import load_dotenv

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()


class Config:
    """Configuration de base commune à tous les environnements"""
    
    # ============================================
    # SÉCURITÉ
    # ============================================
    # ✅ CHARGÉ DEPUIS .env avec fallback sécurisé
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-CHANGE-IN-PRODUCTION'
    
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
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 5 * 1024 * 1024))  # 5MB par défaut
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    IMAGE_MAX_SIZE = 1200
    IMAGE_QUALITY = 85

    # ============================================
    # PAGINATION
    # ============================================
    ITEMS_PER_PAGE_DEFAULT = int(os.environ.get('ITEMS_PER_PAGE_DEFAULT', 24))
    ITEMS_PER_PAGE_RECETTES = int(os.environ.get('ITEMS_PER_PAGE_RECETTES', 20))
    
    # ============================================
    # API / AUTHENTIFICATION
    # ============================================
    # ✅ CHARGÉ DEPUIS .env avec fallback sécurisé
    API_KEY = os.environ.get('API_KEY') or 'dev-api-key-CHANGE-IN-PRODUCTION'
    
    # ============================================
    # CACHE / PERFORMANCE
    # ============================================
    SEND_FILE_MAX_AGE_DEFAULT = 31536000  # 1 an pour les fichiers statiques
    CACHE_TYPE = 'SimpleCache'
    CACHE_DEFAULT_TIMEOUT = 300
    
    COMPRESS_MIMETYPES = [
        'text/html',
        'text/css',
        'text/xml',
        'text/plain',
        'application/json',
        'application/javascript',
        'application/xml'
    ]
    COMPRESS_LEVEL = 6  # 1-9 (6 = bon compromis)
    COMPRESS_MIN_SIZE = 500


class DevelopmentConfig(Config):
    """Configuration pour le développement local"""
    DEBUG = True
    TESTING = False
    SQLALCHEMY_ECHO = True  # Afficher les requêtes SQL en développement
    
    @classmethod
    def init_app(cls, app):
        """Initialisation spécifique au développement"""
        # Afficher un avertissement si les clés par défaut sont utilisées
        if cls.SECRET_KEY == 'dev-secret-key-CHANGE-IN-PRODUCTION':
            app.logger.warning(
                '⚠️  SECRET_KEY par défaut utilisée ! '
                'Définissez SECRET_KEY dans votre fichier .env'
            )
        
        if cls.API_KEY == 'dev-api-key-CHANGE-IN-PRODUCTION':
            app.logger.warning(
                '⚠️  API_KEY par défaut utilisée ! '
                'Définissez API_KEY dans votre fichier .env'
            )


class ProductionConfig(Config):
    """Configuration pour la production"""
    DEBUG = False
    TESTING = False
    SQLALCHEMY_ECHO = False
    
    @classmethod
    def init_app(cls, app):
        """Initialisation spécifique à la production"""
        # ⚠️ VALIDATION STRICTE : En production, les secrets DOIVENT être définis
        
        if not os.environ.get('SECRET_KEY') or cls.SECRET_KEY == 'dev-secret-key-CHANGE-IN-PRODUCTION':
            raise ValueError(
                "⚠️  ERREUR CRITIQUE : SECRET_KEY doit être définie en production!\n"
                "Définissez-la avec: export SECRET_KEY='votre-clef-secrete-complexe'\n"
                "Ou ajoutez-la dans votre fichier .env"
            )
        
        if not os.environ.get('API_KEY') or cls.API_KEY == 'dev-api-key-CHANGE-IN-PRODUCTION':
            raise ValueError(
                "⚠️  ERREUR CRITIQUE : API_KEY doit être définie en production!\n"
                "Définissez-la avec: export API_KEY='votre-clef-api-complexe'\n"
                "Ou ajoutez-la dans votre fichier .env"
            )
        
        # Vérifier que la base de données n'est pas SQLite en production
        if 'sqlite' in cls.SQLALCHEMY_DATABASE_URI.lower():
            app.logger.warning(
                '⚠️  SQLite détectée en production ! '
                'Utilisez PostgreSQL ou MySQL pour de meilleures performances.'
            )


class TestingConfig(Config):
    """Configuration pour les tests unitaires"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'  # Base de données en mémoire
    WTF_CSRF_ENABLED = False  # Désactiver CSRF pour les tests
    SQLALCHEMY_ECHO = False


# ============================================
# HELPER FUNCTIONS
# ============================================

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
    
    Exemples:
        >>> config = get_config('development')
        >>> config = get_config()  # Utilise FLASK_ENV
    """
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    return config_by_name.get(config_name, DevelopmentConfig)


# ============================================
# GUIDE D'UTILISATION
# ============================================
"""
COMMENT UTILISER CETTE CONFIGURATION :

1. DÉVELOPPEMENT LOCAL :
   - Copiez .env.example vers .env
   - Modifiez les valeurs dans .env
   - Lancez l'application : python manage.py

2. PRODUCTION :
   - Définissez les variables d'environnement :
     export FLASK_ENV=production
     export SECRET_KEY="votre-clef-tres-secrete"
     export API_KEY="votre-clef-api-unique"
     export DATABASE_URL="postgresql://user:pass@host/db"
   
   - Ou utilisez un fichier .env (ne pas commiter !)

3. TESTS :
   - export FLASK_ENV=testing
   - pytest

GÉNÉRATION DE CLÉS SÉCURISÉES :
    python -c "import secrets; print(secrets.token_hex(32))"
"""
