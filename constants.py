"""
constants.py
Constantes de l'application Mon Frigo

Contient toutes les constantes métier utilisées dans l'application :
- Catégories d'ingrédients
- Types de recettes
- Saisons (NOUVEAU)
"""

# ============================================
# CATÉGORIES D'INGRÉDIENTS
# ============================================

# Format: (nom, emoji) pour un affichage cohérent
CATEGORIES = [
    ('Fruits', '🍎'),
    ('Légumes', '🥕'),
    ('Viandes', '🥩'),
    ('Poissons', '🐟'),
    ('Produits laitiers', '🥛'),
    ('Œufs', '🥚'),
    ('Céréales', '🌾'),
    ('Légumineuses', '🫘'),
    ('Épices', '🌶️'),
    ('Herbes', '🌿'),
    ('Huiles', '🫒'),
    ('Condiments', '🧂'),
    ('Sucres', '🍯'),
    ('Boissons', '🥤'),
    ('Surgelés', '🧊'),
    ('Conserves', '🥫'),
    ('Pâtes', '🍝'),
    ('Pain', '🍞'),
    ('Fromages', '🧀'),
    ('Charcuterie', '🥓'),
    ('Fruits secs', '🥜'),
    ('Autres', '📦'),
]

# Dict pour accès rapide aux emojis
CATEGORIES_EMOJIS = {nom: emoji for nom, emoji in CATEGORIES}

# Liste des noms de catégories (pour validation)
CATEGORIES_NOMS = [nom for nom, _ in CATEGORIES]


def valider_categorie(categorie: str) -> bool:
    """
    Valide qu'une catégorie est dans la liste des catégories autorisées.
    
    Args:
        categorie: Catégorie à valider
    
    Returns:
        True si valide ou None/vide, False sinon
    """
    if not categorie:
        return True  # Catégorie optionnelle
    return categorie in CATEGORIES_NOMS


# ============================================
# TYPES DE RECETTES
# ============================================

TYPES_RECETTES = [
    'Entrée',
    'Plat principal',
    'Dessert',
    'Accompagnement',
    'Sauce',
    'Soupe',
    'Salade',
    'Petit-déjeuner',
    'Goûter',
    'Apéritif',
    'Boisson',
    'Autre',
]


def valider_type_recette(type_recette: str) -> bool:
    """
    Valide qu'un type de recette est dans la liste autorisée.
    
    Args:
        type_recette: Type à valider
    
    Returns:
        True si valide ou None/vide, False sinon
    """
    if not type_recette:
        return True  # Type optionnel
    return type_recette in TYPES_RECETTES


# ============================================
# SAISONS (NOUVEAU)
# ============================================

# Liste des saisons valides (pour validation)
SAISONS_VALIDES = ['printemps', 'ete', 'automne', 'hiver']

# Saisons avec leurs emojis pour l'affichage (format tuple pour cohérence)
SAISONS = [
    ('printemps', '🌸'),
    ('ete', '☀️'),
    ('automne', '🍂'),
    ('hiver', '❄️'),
]

# Noms complets des saisons pour l'affichage
SAISONS_NOMS = {
    'printemps': 'Printemps',
    'ete': 'Été',
    'automne': 'Automne',
    'hiver': 'Hiver',
}

# Dict pour accès rapide aux emojis
SAISONS_EMOJIS = {
    'printemps': '🌸',
    'ete': '☀️',
    'automne': '🍂',
    'hiver': '❄️',
}


def valider_saison(saison: str) -> bool:
    """
    Valide qu'une saison est dans la liste des saisons autorisées.
    
    Args:
        saison: Saison à valider
    
    Returns:
        True si valide, False sinon
    """
    return saison in SAISONS_VALIDES if saison else True


def valider_liste_saisons(saisons: list) -> bool:
    """
    Valide une liste de saisons.
    
    Args:
        saisons: Liste de saisons à valider
    
    Returns:
        True si toutes les saisons sont valides, False sinon
    """
    if not saisons:
        return True  # Liste vide = valide (toute l'année)
    return all(s in SAISONS_VALIDES for s in saisons)


def get_saison_emoji(saison: str) -> str:
    """
    Retourne l'emoji pour une saison donnée.
    
    Args:
        saison: Code de la saison
    
    Returns:
        Emoji correspondant ou chaîne vide
    """
    return SAISONS_EMOJIS.get(saison, '')


def get_saison_nom(saison: str) -> str:
    """
    Retourne le nom complet d'une saison.
    
    Args:
        saison: Code de la saison
    
    Returns:
        Nom complet ou le code si non trouvé
    """
    return SAISONS_NOMS.get(saison, saison.capitalize() if saison else '')


def formater_saison(saison: str, avec_emoji: bool = True) -> str:
    """
    Formate une saison pour l'affichage.
    
    Args:
        saison: Code de la saison
        avec_emoji: Inclure l'emoji
    
    Returns:
        Chaîne formatée (ex: "🌸 Printemps")
    """
    nom = get_saison_nom(saison)
    if avec_emoji:
        emoji = get_saison_emoji(saison)
        return f"{emoji} {nom}" if emoji else nom
    return nom


def formater_liste_saisons(saisons: list, avec_emoji: bool = True) -> str:
    """
    Formate une liste de saisons pour l'affichage.
    
    Args:
        saisons: Liste de codes de saisons
        avec_emoji: Inclure les emojis
    
    Returns:
        Chaîne formatée (ex: "🌸 Printemps, ☀️ Été") ou "Toute l'année"
    """
    if not saisons:
        return "Toute l'année"
    
    # Trier dans l'ordre naturel des saisons
    ordre = {s: i for i, s in enumerate(SAISONS_VALIDES)}
    saisons_triees = sorted(saisons, key=lambda s: ordre.get(s, 99))
    
    # Si toutes les saisons, simplifier
    if len(saisons_triees) == 4:
        return "Toute l'année"
    
    return ", ".join(formater_saison(s, avec_emoji) for s in saisons_triees)
