"""
utils/files.py
Utilitaires pour la gestion des fichiers (uploads, validation, etc.)
"""
import os
from werkzeug.utils import secure_filename
from flask import current_app


def allowed_file(filename):
    """
    Vérifie si l'extension du fichier est autorisée
    
    Args:
        filename: Nom du fichier à vérifier
    
    Returns:
        bool: True si l'extension est autorisée
    
    Example:
        >>> allowed_file('photo.jpg')
        True
        >>> allowed_file('script.exe')
        False
    """
    if not filename or '.' not in filename:
        return False
    
    extension = filename.rsplit('.', 1)[1].lower()
    allowed_extensions = current_app.config.get('ALLOWED_EXTENSIONS', set())
    
    return extension in allowed_extensions


def save_uploaded_file(file, prefix='file', subfolder=''):
    """
    Sauvegarde un fichier uploadé de manière sécurisée
    
    Args:
        file: Fichier depuis request.files
        prefix: Préfixe pour le nom du fichier (ex: 'ing_', 'rec_')
        subfolder: Sous-dossier dans UPLOAD_FOLDER (optionnel)
    
    Returns:
        str: Chemin relatif du fichier sauvegardé ou None si échec
    
    Example:
        >>> file = request.files['image']
        >>> filepath = save_uploaded_file(file, prefix='ing_tomate')
        >>> # Retourne: 'static/uploads/ing_tomate_photo.jpg'
    """
    if not file or file.filename == '':
        return None
    
    if not allowed_file(file.filename):
        return None
    
    # Créer un nom de fichier sécurisé
    original_filename = secure_filename(file.filename)
    filename = f"{prefix}_{original_filename}"
    
    # Construire le chemin complet
    upload_folder = current_app.config.get('UPLOAD_FOLDER', 'static/uploads')
    
    if subfolder:
        upload_folder = os.path.join(upload_folder, subfolder)
    
    # Créer le dossier s'il n'existe pas
    full_upload_path = os.path.join(current_app.root_path, upload_folder)
    os.makedirs(full_upload_path, exist_ok=True)
    
    # Chemin complet du fichier
    filepath = os.path.join(upload_folder, filename)
    full_filepath = os.path.join(current_app.root_path, filepath)
    
    # Sauvegarder le fichier
    try:
        file.save(full_filepath)
        return filepath
    except Exception as e:
        print(f"Erreur lors de la sauvegarde du fichier : {e}")
        return None


def delete_file(filepath):
    """
    Supprime un fichier de manière sécurisée
    
    Args:
        filepath: Chemin relatif du fichier (ex: 'static/uploads/image.jpg')
    
    Returns:
        bool: True si suppression réussie, False sinon
    """
    if not filepath:
        return False
    
    try:
        full_path = os.path.join(current_app.root_path, filepath)
        if os.path.exists(full_path):
            os.remove(full_path)
            return True
    except Exception as e:
        print(f"Erreur lors de la suppression du fichier {filepath}: {e}")
    
    return False


def get_file_extension(filename):
    """
    Extrait l'extension d'un fichier
    
    Args:
        filename: Nom du fichier
    
    Returns:
        str: Extension en minuscules (sans le point) ou None
    """
    if not filename or '.' not in filename:
        return None
    
    return filename.rsplit('.', 1)[1].lower()
