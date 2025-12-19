"""
utils/units.py
Gestion des unités et conversions pour les ingrédients

Ce module gère la conversion entre les unités natives (g, ml, pièce)
et les unités de base pour les calculs (g/ml).

PRINCIPE FONDAMENTAL :
- Les quantités sont STOCKÉES dans l'unité native de l'ingrédient
  (ex: 2 œufs stockés comme 2, pas 120g)
- Pour les calculs (nutrition, coût basé sur €/g), on convertit vers grammes
- Pour l'affichage, on utilise l'unité native avec formatage approprié
"""

# Unités supportées
UNITES_SUPPORTEES = ['g', 'ml', 'pièce']


def get_step_for_unite(unite: str) -> str:
    """
    Retourne le step HTML approprié pour un input de quantité selon l'unité.
    
    Args:
        unite: L'unité de l'ingrédient
    
    Returns:
        La valeur du step pour l'input HTML
    
    Examples:
        >>> get_step_for_unite('pièce')
        '0.5'  # Permet les demi-pièces
        >>> get_step_for_unite('g')
        '1'
    """
    if unite == 'pièce':
        return '0.5'  # Permet les demi-pièces
    return '1'


def valider_unite(unite: str) -> bool:
    """
    Vérifie si une unité est valide.
    
    Args:
        unite: L'unité à valider
    
    Returns:
        True si l'unité est supportée
    """
    return unite in UNITES_SUPPORTEES


def convertir_vers_grammes(quantite: float, ingredient) -> float:
    """
    Convertit une quantité dans l'unité native de l'ingrédient vers des grammes/ml.
    
    Utilisé pour :
    - Calculs nutritionnels (basés sur 100g)
    - Comparaison avec le stock (stocké en unité native)
    
    Args:
        quantite: Quantité dans l'unité native de l'ingrédient
        ingredient: Objet Ingredient avec unite et poids_piece
    
    Returns:
        Quantité en grammes (ou ml pour les liquides)
    """
    if not quantite or quantite <= 0:
        return 0
    
    unite = getattr(ingredient, 'unite', 'g')
    poids_piece = getattr(ingredient, 'poids_piece', None)
    
    if unite == 'pièce' and poids_piece and poids_piece > 0:
        # Convertir pièces → grammes
        return quantite * poids_piece
    
    # Pour g et ml, la quantité est déjà en unité de base
    return quantite


def convertir_depuis_grammes(quantite_grammes: float, ingredient) -> float:
    """
    Convertit une quantité en grammes vers l'unité native de l'ingrédient.
    
    Args:
        quantite_grammes: Quantité en grammes
        ingredient: Objet Ingredient avec unite et poids_piece
    
    Returns:
        Quantité dans l'unité native de l'ingrédient
    """
    if not quantite_grammes or quantite_grammes <= 0:
        return 0
    
    unite = getattr(ingredient, 'unite', 'g')
    poids_piece = getattr(ingredient, 'poids_piece', None)
    
    if unite == 'pièce' and poids_piece and poids_piece > 0:
        # Convertir grammes → pièces
        return quantite_grammes / poids_piece
    
    return quantite_grammes


def formater_quantite(quantite: float, ingredient, avec_unite: bool = True) -> str:
    """
    Formate une quantité pour l'affichage.
    
    La quantité est supposée être dans l'unité native de l'ingrédient.
    
    Args:
        quantite: Quantité dans l'unité native
        ingredient: Objet Ingredient
        avec_unite: Inclure l'unité dans le formatage
    
    Returns:
        String formatée (ex: "2 pièces", "150 g", "200 ml")
    """
    if not quantite or quantite <= 0:
        return "0" if not avec_unite else "0"
    
    unite = getattr(ingredient, 'unite', 'g')
    nom = getattr(ingredient, 'nom', '')
    
    # Formatage du nombre
    if quantite == int(quantite):
        quantite_str = str(int(quantite))
    elif quantite < 1:
        quantite_str = f"{quantite:.2f}"
    else:
        quantite_str = f"{quantite:.1f}".rstrip('0').rstrip('.')
    
    if not avec_unite:
        return quantite_str
    
    # Formatage de l'unité
    if unite == 'pièce':
        # Pluraliser intelligemment
        if quantite > 1:
            return f"{quantite_str} {_pluraliser(nom)}"
        return f"{quantite_str} {nom}"
    
    return f"{quantite_str} {unite}"


def _pluraliser(nom: str) -> str:
    """
    Pluralise un nom français.
    
    Args:
        nom: Nom au singulier
    
    Returns:
        Nom au pluriel
    """
    if not nom:
        return nom
    
    nom_lower = nom.lower()
    
    # Exceptions courantes
    exceptions = {
        'oeuf': 'oeufs',
        'œuf': 'œufs',
        'chou': 'choux',
        'bijou': 'bijoux',
        'genou': 'genoux',
        'hibou': 'hiboux',
        'joujou': 'joujoux',
        'pou': 'poux'
    }
    
    if nom_lower in exceptions:
        resultat = exceptions[nom_lower]
        # Conserver la casse d'origine
        if nom[0].isupper():
            return resultat.capitalize()
        return resultat
    
    # Déjà au pluriel
    if nom_lower.endswith(('s', 'x', 'z')):
        return nom
    
    # Terminaisons spéciales
    if nom_lower.endswith(('au', 'eau', 'eu')):
        return nom + 'x'
    
    if nom_lower.endswith('al'):
        return nom[:-2] + 'aux'
    
    # Règle générale
    return nom + 's'


def calculer_prix_total(quantite: float, ingredient) -> float:
    """
    Calcule le prix total pour une quantité d'ingrédient.
    
    La quantité est supposée être dans l'unité native de l'ingrédient.
    Le prix_unitaire est stocké par unité native.
    
    Args:
        quantite: Quantité dans l'unité native
        ingredient: Objet Ingredient avec prix_unitaire
    
    Returns:
        Prix total arrondi à 2 décimales
    """
    if not quantite or quantite <= 0:
        return 0
    
    prix_unitaire = getattr(ingredient, 'prix_unitaire', 0) or 0
    
    if prix_unitaire <= 0:
        return 0
    
    return round(quantite * prix_unitaire, 2)


def formater_prix_unitaire(ingredient) -> str:
    """
    Formate le prix unitaire pour l'affichage.
    
    Args:
        ingredient: Objet Ingredient
    
    Returns:
        String formatée (ex: "1.50€/pièce", "5.00€/kg", "3.00€/L")
    """
    prix = getattr(ingredient, 'prix_unitaire', 0) or 0
    unite = getattr(ingredient, 'unite', 'g')
    
    if prix <= 0:
        return "Prix non renseigné"
    
    if unite == 'pièce':
        return f"{prix:.2f}€/pièce"
    elif unite == 'g':
        # Convertir €/g en €/kg pour l'affichage
        prix_kg = prix * 1000
        return f"{prix_kg:.2f}€/kg"
    elif unite == 'ml':
        # Convertir €/ml en €/L pour l'affichage
        prix_l = prix * 1000
        return f"{prix_l:.2f}€/L"
    else:
        return f"{prix:.2f}€/{unite}"
