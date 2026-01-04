"""
utils/files.py (VERSION OPTIMISÉE)
Gestion des fichiers avec compression automatique des images

✅ OPTIMISATION TECHNIQUE - Compression des images intégrée
- Remplace l'ancienne version de save_uploaded_file
- Ajoute automatiquement la compression si Pillow est installé
- Rétrocompatible avec le code existant

USAGE:
    # Exactement comme avant - la compression est automatique
    filepath = save_uploaded_file(file, prefix='rec_poulet')
"""
import os
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import current_app

# Importer les fonctions d'optimisation d'image
try:
    from utils.images import (
        save_optimized_image, 
        allowed_file,
        PILLOW_AVAILABLE
    )
    IMAGES_MODULE_AVAILABLE = True
except ImportError:
    IMAGES_MODULE_AVAILABLE = False
    PILLOW_AVAILABLE = False


def get_upload_folder():
    """Retourne le chemin complet du dossier d'upload."""
    upload_folder = current_app.config.get('UPLOAD_FOLDER', 'static/uploads')
    full_path = os.path.join(current_app.root_path, upload_folder)
    os.makedirs(full_path, exist_ok=True)
    return full_path


def allowed_file_basic(filename):
    """
    Vérifie si l'extension est autorisée (version basique).
    """
    if not filename or '.' not in filename:
        return False
    
    allowed = current_app.config.get(
        'ALLOWED_EXTENSIONS', 
        {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    )
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in allowed


def generate_unique_filename(original_filename, prefix=''):
    """
    Génère un nom de fichier unique.
    
    Args:
        original_filename: Nom original du fichier
        prefix: Préfixe optionnel
    
    Returns:
        Nom de fichier unique et sécurisé
    """
    if not original_filename or '.' not in original_filename:
        ext = 'jpg'
    else:
        ext = original_filename.rsplit('.', 1)[1].lower()
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    
    if prefix:
        # Nettoyer le préfixe
        safe_prefix = secure_filename(prefix).replace(' ', '_')[:50]
        return f"{safe_prefix}_{timestamp}.{ext}"
    
    return f"file_{timestamp}.{ext}"


def save_uploaded_file(file, prefix='', optimize=True):
    """
    Sauvegarde un fichier uploadé avec optimisation automatique.
    
    ✅ VERSION OPTIMISÉE - Compatible avec l'ancien code
    
    Args:
        file: Fichier uploadé (FileStorage)
        prefix: Préfixe pour le nom du fichier
        optimize: Optimiser l'image si possible (défaut: True)
    
    Returns:
        Chemin relatif du fichier sauvegardé (pour la DB)
        ou None si erreur/fichier invalide
    
    Examples:
        # Usage simple (comme avant)
        filepath = save_uploaded_file(file, prefix='rec_poulet')
        
        # Sans optimisation
        filepath = save_uploaded_file(file, prefix='doc', optimize=False)
    """
    # Vérifications de base
    if not file or not file.filename:
        return None
    
    filename = file.filename
    
    # Vérifier l'extension
    check_func = allowed_file if IMAGES_MODULE_AVAILABLE else allowed_file_basic
    if not check_func(filename):
        current_app.logger.warning(f'Extension non autorisée: {filename}')
        return None
    
    # Si le module images est disponible et optimisation demandée
    if IMAGES_MODULE_AVAILABLE and optimize and PILLOW_AVAILABLE:
        # Utiliser la fonction optimisée
        max_size = current_app.config.get('IMAGE_MAX_SIZE', 1200)
        quality = current_app.config.get('IMAGE_QUALITY', 85)
        create_thumb = current_app.config.get('IMAGE_CREATE_THUMBNAILS', False)
        
        return save_optimized_image(
            file,
            prefix=prefix,
            max_size=max_size,
            quality=quality,
            create_thumb=create_thumb
        )
    
    # Fallback: sauvegarde basique sans optimisation
    try:
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'static/uploads')
        full_path = os.path.join(current_app.root_path, upload_folder)
        os.makedirs(full_path, exist_ok=True)
        
        new_filename = generate_unique_filename(filename, prefix)
        filepath = os.path.join(full_path, new_filename)
        
        file.save(filepath)
        
        relative_path = os.path.join(upload_folder, new_filename)
        current_app.logger.info(f'Fichier sauvegardé: {relative_path}')
        
        return relative_path
    
    except Exception as e:
        current_app.logger.error(f'Erreur sauvegarde fichier: {e}')
        return None


def delete_file(filepath):
    """
    Supprime un fichier du système de fichiers.
    
    Args:
        filepath: Chemin relatif du fichier (ex: 'static/uploads/image.jpg')
    
    Returns:
        True si supprimé, False sinon
    """
    if not filepath:
        return False
    
    try:
        # Construire le chemin complet
        if filepath.startswith('static/'):
            full_path = os.path.join(current_app.root_path, filepath)
        else:
            full_path = os.path.join(
                current_app.root_path, 
                current_app.config.get('UPLOAD_FOLDER', 'static/uploads'),
                os.path.basename(filepath)
            )
        
        if os.path.exists(full_path):
            os.remove(full_path)
            current_app.logger.info(f'Fichier supprimé: {filepath}')
            
            # Supprimer aussi la miniature si elle existe
            thumb_path = full_path.replace('.', '_thumb.', 1)
            if os.path.exists(thumb_path):
                os.remove(thumb_path)
            
            return True
        else:
            current_app.logger.warning(f'Fichier non trouvé: {filepath}')
            return False
    
    except Exception as e:
        current_app.logger.error(f'Erreur suppression fichier {filepath}: {e}')
        return False


def get_file_size(filepath):
    """
    Retourne la taille d'un fichier en octets.
    
    Args:
        filepath: Chemin du fichier
    
    Returns:
        Taille en octets ou 0 si erreur
    """
    try:
        if filepath.startswith('static/'):
            full_path = os.path.join(current_app.root_path, filepath)
        else:
            full_path = filepath
        
        if os.path.exists(full_path):
            return os.path.getsize(full_path)
    except:
        pass
    return 0


def format_file_size(size_bytes):
    """
    Formate une taille en bytes en format lisible.
    
    Args:
        size_bytes: Taille en octets
    
    Returns:
        String formaté (ex: "1.5 MB")
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
