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


# ============================================
# SAISONS (NOUVEAU)
# ============================================

# Liste des saisons valides (pour validation)
SAISONS_VALIDES = ['printemps', 'ete', 'automne', 'hiver']

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

DATES_SAISONS = {
    'printemps': (20, 3),   # 20 mars
    'ete': (21, 6),         # 21 juin
    'automne': (22, 9),     # 22 septembre
    'hiver': (21, 12),      # 21 décembre
}



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



