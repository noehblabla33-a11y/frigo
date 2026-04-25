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

CATEGORIES_EMOJIS = {nom: emoji for nom, emoji in CATEGORIES}

CATEGORIES_NOMS = [nom for nom, _ in CATEGORIES]

ML_PAR_CS = 15
CATEGORIE_HUILES = 'Huiles'

G_PAR_PINCEE = 0.5
CATEGORIES_PINCEES = ['Épices', 'Condiments']


TYPES_RECETTES = [
    'Entrée',
    'Plat principal',
    'Dessert',
    'Sauce',
    'Soupe',
    'Salade',
    'Apéritif',
    'Boisson',
    'Autre',
]


SAISONS_VALIDES = ['printemps', 'ete', 'automne', 'hiver']

SAISONS_NOMS = {
    'printemps': 'Printemps',
    'ete': 'Été',
    'automne': 'Automne',
    'hiver': 'Hiver',
}

SAISONS_EMOJIS = {
    'printemps': '🌸',
    'ete': '☀️',
    'automne': '🍂',
    'hiver': '❄️',
}

DATES_SAISONS = {
    'printemps': (20, 3),
    'ete': (21, 6),
    'automne': (22, 9),
    'hiver': (21, 12),
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
