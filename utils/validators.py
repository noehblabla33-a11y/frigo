"""
utils/validators.py
Validateurs centralisés pour les formulaires

Ce module regroupe les fonctions de validation réutilisées
dans plusieurs routes, garantissant une cohérence des règles métier.
"""

from flask import flash
from models.models import Ingredient, Recette
from typing import Optional, Tuple, List


# ============================================
# VALIDATION UNICITÉ
# ============================================

def validate_unique_ingredient(nom: str, exclude_id: Optional[int] = None) -> bool:
    """
    Vérifie qu'un ingrédient n'existe pas déjà avec ce nom.
    
    Args:
        nom: Nom de l'ingrédient à vérifier
        exclude_id: ID à exclure (pour modification)
    
    Returns:
        True si valide (n'existe pas), False sinon
    
    Example:
        if not validate_unique_ingredient(nom):
            return redirect(url_for('ingredients.liste'))
    """
    query = Ingredient.query.filter_by(nom=nom)
    
    if exclude_id:
        query = query.filter(Ingredient.id != exclude_id)
    
    if query.first():
        flash(f'L\'ingrédient "{nom}" existe déjà !', 'danger')
        return False
    
    return True


def validate_unique_recette(nom: str, exclude_id: Optional[int] = None) -> bool:
    """
    Vérifie qu'une recette n'existe pas déjà avec ce nom.
    
    Args:
        nom: Nom de la recette à vérifier
        exclude_id: ID à exclure (pour modification)
    
    Returns:
        True si valide, False sinon
    """
    query = Recette.query.filter_by(nom=nom)
    
    if exclude_id:
        query = query.filter(Recette.id != exclude_id)
    
    if query.first():
        flash(f'La recette "{nom}" existe déjà !', 'danger')
        return False
    
    return True


# ============================================
# VALIDATION RELATIONS
# ============================================

def validate_ingredient_not_used(ingredient: Ingredient) -> Tuple[bool, List[str]]:
    """
    Vérifie qu'un ingrédient n'est pas utilisé dans des recettes.
    
    Args:
        ingredient: L'ingrédient à vérifier
    
    Returns:
        Tuple (peut_supprimer: bool, noms_recettes: list)
    """
    recettes_utilisees = []
    
    for ing_rec in ingredient.recettes:
        recette = ing_rec.recette
        if recette:
            recettes_utilisees.append(recette.nom)
    
    if recettes_utilisees:
        # Limiter l'affichage à 3 recettes
        if len(recettes_utilisees) <= 3:
            recettes_str = ', '.join(recettes_utilisees)
        else:
            recettes_str = ', '.join(recettes_utilisees[:3]) + f' et {len(recettes_utilisees) - 3} autre(s)'
        
        flash(
            f'Impossible de supprimer "{ingredient.nom}" : '
            f'utilisé dans {len(recettes_utilisees)} recette(s) ({recettes_str})',
            'danger'
        )
        return False, recettes_utilisees
    
    return True, []


def validate_recette_not_planned(recette: Recette) -> Tuple[bool, int]:
    """
    Vérifie qu'une recette n'a pas de planifications en cours.
    
    Args:
        recette: La recette à vérifier
    
    Returns:
        Tuple (peut_supprimer: bool, nb_planifications: int)
    
    Note:
        Cette fonction informe mais ne bloque pas la suppression.
        Les planifications seront supprimées en cascade.
    """
    nb_planifications = len([p for p in recette.planifications if not p.preparee])
    
    if nb_planifications > 0:
        flash(
            f'Attention : "{recette.nom}" a {nb_planifications} planification(s) en cours. '
            f'Elles seront également supprimées.',
            'warning'
        )
    
    return True, nb_planifications


# ============================================
# VALIDATION QUANTITÉS
# ============================================

def validate_quantite_positive(quantite: float, nom_champ: str = 'quantité') -> bool:
    """
    Vérifie qu'une quantité est positive.
    
    Args:
        quantite: Valeur à vérifier
        nom_champ: Nom du champ pour le message d'erreur
    
    Returns:
        True si valide
    """
    if quantite is None or quantite < 0:
        flash(f'La {nom_champ} doit être un nombre positif.', 'danger')
        return False
    
    return True


def validate_quantite_stock_suffisant(
    ingredient_id: int, 
    quantite_requise: float,
    nom_ingredient: str = None
) -> bool:
    """
    Vérifie qu'il y a assez de stock pour une opération.
    
    Args:
        ingredient_id: ID de l'ingrédient
        quantite_requise: Quantité nécessaire
        nom_ingredient: Nom pour le message (optionnel)
    
    Returns:
        True si stock suffisant
    """
    from models.models import StockFrigo
    
    stock = StockFrigo.query.filter_by(ingredient_id=ingredient_id).first()
    quantite_dispo = stock.quantite if stock else 0
    
    if quantite_dispo < quantite_requise:
        nom = nom_ingredient or f'l\'ingrédient (ID: {ingredient_id})'
        flash(
            f'Stock insuffisant pour {nom} : '
            f'{quantite_dispo} disponible(s), {quantite_requise} requis(es).',
            'warning'
        )
        return False
    
    return True


# ============================================
# VALIDATION CATÉGORIES ET TYPES
# ============================================

def validate_categorie(categorie: str, categories_valides: List[Tuple]) -> bool:
    """
    Vérifie qu'une catégorie est valide.
    
    Args:
        categorie: Catégorie à vérifier
        categories_valides: Liste de tuples (nom, icone) depuis constants.py
    
    Returns:
        True si valide
    """
    if not categorie:
        return True  # Catégorie optionnelle
    
    noms_valides = [cat[0] for cat in categories_valides]
    
    if categorie not in noms_valides:
        flash(f'Catégorie invalide : "{categorie}"', 'danger')
        return False
    
    return True


def validate_type_recette(type_recette: str, types_valides: List[str]) -> bool:
    """
    Vérifie qu'un type de recette est valide.
    
    Args:
        type_recette: Type à vérifier
        types_valides: Liste des types depuis constants.py
    
    Returns:
        True si valide
    """
    if not type_recette:
        return True  # Type optionnel
    
    if type_recette not in types_valides:
        flash(f'Type de recette invalide : "{type_recette}"', 'danger')
        return False
    
    return True


# ============================================
# VALIDATION FICHIERS
# ============================================

def validate_image_file(file, max_size_mb: float = 5) -> bool:
    """
    Vérifie qu'un fichier uploadé est une image valide.
    
    Args:
        file: FileStorage de Flask
        max_size_mb: Taille maximale en MB
    
    Returns:
        True si valide
    """
    if not file or not file.filename:
        return True  # Pas de fichier = optionnel
    
    # Vérifier l'extension
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    
    if ext not in allowed_extensions:
        flash(
            f'Format de fichier non supporté : .{ext}. '
            f'Formats acceptés : {", ".join(allowed_extensions)}',
            'danger'
        )
        return False
    
    # Vérifier la taille (approximatif car stream)
    file.seek(0, 2)  # Aller à la fin
    size = file.tell()
    file.seek(0)  # Revenir au début
    
    if size > max_size_mb * 1024 * 1024:
        flash(f'Fichier trop volumineux. Maximum : {max_size_mb} MB', 'danger')
        return False
    
    return True


# ============================================
# VALIDATION COMPOSITE
# ============================================

def validate_ingredient_form(
    nom: str,
    categorie: str = None,
    categories_valides: List[Tuple] = None,
    exclude_id: Optional[int] = None
) -> bool:
    """
    Valide un formulaire d'ingrédient complet.
    
    Args:
        nom: Nom de l'ingrédient
        categorie: Catégorie (optionnel)
        categories_valides: Liste des catégories valides
        exclude_id: ID à exclure pour la modification
    
    Returns:
        True si tout est valide
    """
    if not nom or not nom.strip():
        flash('Le nom de l\'ingrédient est requis.', 'danger')
        return False
    
    if not validate_unique_ingredient(nom, exclude_id):
        return False
    
    if categorie and categories_valides:
        if not validate_categorie(categorie, categories_valides):
            return False
    
    return True


def validate_recette_form(
    nom: str,
    type_recette: str = None,
    types_valides: List[str] = None,
    exclude_id: Optional[int] = None
) -> bool:
    """
    Valide un formulaire de recette complet.
    
    Args:
        nom: Nom de la recette
        type_recette: Type (optionnel)
        types_valides: Liste des types valides
        exclude_id: ID à exclure pour la modification
    
    Returns:
        True si tout est valide
    """
    if not nom or not nom.strip():
        flash('Le nom de la recette est requis.', 'danger')
        return False
    
    if not validate_unique_recette(nom, exclude_id):
        return False
    
    if type_recette and types_valides:
        if not validate_type_recette(type_recette, types_valides):
            return False
    
    return True
