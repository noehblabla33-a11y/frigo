"""
constants.py
Constantes métier de l'application
Contient les données "business" : catégories, types, choix utilisateur, etc.
"""

# ============================================
# CATÉGORIES D'INGRÉDIENTS
# ============================================
CATEGORIES = [
    ('Légumes', '🥬'),
    ('Fruits', '🍎'),
    ('Viandes', '🥩'),
    ('Poissons', '🐟'),
    ('Produits laitiers', '🥛'),
    ('Féculents', '🍚'),
    ('Épices et herbes', '🌿'),
    ('Condiments', '🧂'),
    ('Boissons', '🥤'),
    ('Boulangerie', '🥖'),
    ('Autres', '📦')
]

# Liste des noms de catégories uniquement (utile pour validation)
CATEGORIES_NOMS = [cat[0] for cat in CATEGORIES]

# Dictionnaire {nom: emoji} pour accès rapide
CATEGORIES_DICT = {cat[0]: cat[1] for cat in CATEGORIES}


# ============================================
# TYPES DE RECETTES
# ============================================
TYPES_RECETTES = [
    'Entrée',
    'Plat principal',
    'Accompagnement',
    'Dessert',
    'Petit-déjeuner',
    'Salade',
    'Soupe',
    'Au four',
    'À la poêle',
    'À la casserole',
    'Sans cuisson',
    'Boisson',
    'Autre'
]


# ============================================
# UNITÉS DE MESURE
# ============================================
UNITES_MESURE = [
    ('g', 'grammes (g)'),
    ('cl', 'centilitres (cl)'),
    ('pièce', 'pièce(s)'),
    ('c. à soupe', 'cuillère(s) à soupe'),
    ('c. à café', 'cuillère(s) à café'),
]

# Liste des codes d'unités uniquement
UNITES_CODES = [unite[0] for unite in UNITES_MESURE]


# ============================================
# FONCTIONS UTILITAIRES POUR CONSTANTES
# ============================================

def get_categorie_emoji(nom_categorie):
    """
    Retourne l'emoji d'une catégorie par son nom
    
    Args:
        nom_categorie: Nom de la catégorie (ex: "Légumes")
    
    Returns:
        str: Emoji correspondant ou '📦' par défaut
    """
    return CATEGORIES_DICT.get(nom_categorie, '📦')


def valider_categorie(nom_categorie):
    """
    Vérifie si une catégorie existe
    
    Args:
        nom_categorie: Nom de la catégorie à valider
    
    Returns:
        bool: True si la catégorie existe
    """
    return nom_categorie in CATEGORIES_NOMS


def valider_type_recette(type_recette):
    """
    Vérifie si un type de recette existe
    
    Args:
        type_recette: Type de recette à valider
    
    Returns:
        bool: True si le type existe
    """
    return type_recette in TYPES_RECETTES


def valider_unite(unite):
    """
    Vérifie si une unité de mesure existe
    
    Args:
        unite: Code de l'unité à valider
    
    Returns:
        bool: True si l'unité existe
    """
    return unite in UNITES_CODES
