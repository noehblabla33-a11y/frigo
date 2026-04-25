import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Configuration de base commune à tous les environnements."""

    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-CHANGE-IN-PRODUCTION'

    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///frigo.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False

    UPLOAD_FOLDER = 'static/uploads'
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 5 * 1024 * 1024))
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    IMAGE_MAX_SIZE = 1200
    IMAGE_QUALITY = 85

    ITEMS_PER_PAGE_DEFAULT = int(os.environ.get('ITEMS_PER_PAGE_DEFAULT', 24))
    ITEMS_PER_PAGE_RECETTES = int(os.environ.get('ITEMS_PER_PAGE_RECETTES', 20))

    API_KEY = os.environ.get('API_KEY') or 'dev-api-key-CHANGE-IN-PRODUCTION'

    SEND_FILE_MAX_AGE_DEFAULT = 31536000
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
    COMPRESS_LEVEL = 6
    COMPRESS_MIN_SIZE = 500


class DevelopmentConfig(Config):
    """Configuration pour le développement local."""
    DEBUG = True
    TESTING = False
    SQLALCHEMY_ECHO = True

    @classmethod
    def init_app(cls, app):
        """Initialisation spécifique au développement."""
        if cls.SECRET_KEY == 'dev-secret-key-CHANGE-IN-PRODUCTION':
            app.logger.warning(
                'SECRET_KEY par défaut utilisée ! '
                'Définissez SECRET_KEY dans votre fichier .env'
            )

        if cls.API_KEY == 'dev-api-key-CHANGE-IN-PRODUCTION':
            app.logger.warning(
                'API_KEY par défaut utilisée ! '
                'Définissez API_KEY dans votre fichier .env'
            )


class ProductionConfig(Config):
    """Configuration pour la production."""
    DEBUG = False
    TESTING = False
    SQLALCHEMY_ECHO = False

    @classmethod
    def init_app(cls, app):
        """Initialisation spécifique à la production."""
        if not os.environ.get('SECRET_KEY') or cls.SECRET_KEY == 'dev-secret-key-CHANGE-IN-PRODUCTION':
            raise ValueError(
                "ERREUR CRITIQUE : SECRET_KEY doit être définie en production!\n"
                "Définissez-la avec: export SECRET_KEY='votre-clef-secrete-complexe'\n"
                "Ou ajoutez-la dans votre fichier .env"
            )

        if not os.environ.get('API_KEY') or cls.API_KEY == 'dev-api-key-CHANGE-IN-PRODUCTION':
            raise ValueError(
                "ERREUR CRITIQUE : API_KEY doit être définie en production!\n"
                "Définissez-la avec: export API_KEY='votre-clef-api-complexe'\n"
                "Ou ajoutez-la dans votre fichier .env"
            )

        if 'sqlite' in cls.SQLALCHEMY_DATABASE_URI.lower():
            app.logger.warning(
                'SQLite détectée en production ! '
                'Utilisez PostgreSQL ou MySQL pour de meilleures performances.'
            )


class TestingConfig(Config):
    """Configuration pour les tests unitaires."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_ECHO = False


config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config(config_name=None):
    """
    Récupère la configuration appropriée.

    Args:
        config_name: 'development', 'production', 'testing' ou None (utilise FLASK_ENV)

    Returns:
        Classe de configuration appropriée
    """
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    return config_by_name.get(config_name, DevelopmentConfig)
