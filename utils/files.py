ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    """Vérifie si l'extension du fichier est autorisée"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_uploaded_file(file, prefix, upload_folder, root_path):
    """Sauvegarde un fichier uploadé de manière sécurisée"""
    from werkzeug.utils import secure_filename
    import os
    
    if file and file.filename != '' and allowed_file(file.filename):
        filename = secure_filename(f"{prefix}_{file.filename}")
        filepath = os.path.join(upload_folder, filename)
        file.save(os.path.join(root_path, filepath))
        return filepath
    return None
