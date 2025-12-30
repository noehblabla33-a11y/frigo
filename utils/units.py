"""
utils/units.py
Fonctions utilitaires pour le formatage des quantités et des prix

SYSTÈME D'UNITÉS (RÉALITÉ DU STOCKAGE) :
- Le prix est TOUJOURS stocké en €/g (ou €/ml), même pour les pièces
- Pour les pièces, on stocke €/g et on utilise poids_piece pour reconvertir
- C'est le comportement du price-helper.js qui fait cette conversion

✅ CORRIGÉ : Reconversion correcte de €/g vers €/pièce à l'affichage
"""


def formater_quantite(quantite: float, ingredient) -> str:
    """
    Formate une quantité pour l'affichage selon l'unité de l'ingrédient.
    
    Args:
        quantite: La quantité à formater
        ingredient: L'objet Ingredient (doit avoir .unite)
    
    Returns:
        str: La quantité formatée (ex: "2 pièces", "500g", "250ml")
    """
    if quantite is None or quantite == 0:
        return "0"
    
    unite = ingredient.unite if ingredient else 'g'
    
    if unite == 'pièce':
        # Afficher les pièces en entier ou demi
        if quantite == int(quantite):
            return f"{int(quantite)} {'pièce' if quantite == 1 else 'pièces'}"
        else:
            return f"{quantite:.1f} pièces"
    
    elif unite == 'g':
        # Convertir en kg si > 1000g
        if quantite >= 1000:
            return f"{quantite / 1000:.2f}kg"
        elif quantite == int(quantite):
            return f"{int(quantite)}g"
        else:
            return f"{quantite:.1f}g"
    
    elif unite == 'ml':
        # Convertir en L si > 1000ml
        if quantite >= 1000:
            return f"{quantite / 1000:.2f}L"
        elif quantite == int(quantite):
            return f"{int(quantite)}ml"
        else:
            return f"{quantite:.1f}ml"
    
    else:
        # Unité inconnue
        return f"{quantite} {unite}"


def formater_prix_unitaire(ingredient) -> str:
    """
    Formate le prix unitaire d'un ingrédient pour l'affichage.
    
    ⚠️ ATTENTION - LOGIQUE DE STOCKAGE :
    Le prix est TOUJOURS stocké en €/g (ou €/ml par le price-helper.js)
    même pour les ingrédients avec unite='pièce'.
    
    Pour les pièces avec poids_piece défini :
    - prix_unitaire = prix_par_piece / poids_piece (stocké en €/g)
    - Donc prix_par_piece = prix_unitaire × poids_piece
    
    Args:
        ingredient: L'objet Ingredient
    
    Returns:
        str: Le prix formaté (ex: "15.50€/kg", "2.30€/L", "1.35€/pièce")
    """
    if not ingredient:
        return "Prix non renseigné"
    
    prix = ingredient.prix_unitaire
    unite = ingredient.unite
    poids_piece = getattr(ingredient, 'poids_piece', None)
    
    if not prix or prix <= 0:
        return "Prix non renseigné"
    
    if unite == 'pièce':
        # ✅ CORRIGÉ : Pour les pièces, le prix est stocké en €/g
        # On doit reconvertir en €/pièce en multipliant par poids_piece
        if poids_piece and poids_piece > 0:
            prix_piece = prix * poids_piece
            return f"{prix_piece:.2f}€/pièce"
        else:
            # Si pas de poids_piece, on affiche le prix brut avec une note
            # (cas anormal mais on gère)
            return f"{prix:.2f}€/pièce"
    
    elif unite == 'g':
        # Pour les grammes, convertir en €/kg pour l'affichage
        prix_kg = prix * 1000
        return f"{prix_kg:.2f}€/kg"
    
    elif unite == 'ml':
        # Pour les millilitres, convertir en €/L pour l'affichage
        prix_l = prix * 1000
        return f"{prix_l:.2f}€/L"
    
    else:
        # Unité inconnue, afficher tel quel
        return f"{prix:.4f}€/{unite}"


def calculer_prix_affichage_piece(ingredient) -> float:
    """
    Calcule le prix par pièce pour l'affichage.
    
    Le prix est stocké en €/g, cette fonction reconvertit en €/pièce.
    
    Args:
        ingredient: L'objet Ingredient
    
    Returns:
        float: Le prix par pièce, ou 0 si non calculable
    """
    if not ingredient or not ingredient.prix_unitaire:
        return 0
    
    if ingredient.unite != 'pièce':
        return ingredient.prix_unitaire
    
    poids_piece = getattr(ingredient, 'poids_piece', None)
    if poids_piece and poids_piece > 0:
        return ingredient.prix_unitaire * poids_piece
    
    return ingredient.prix_unitaire


def calculer_valeur_stock(ingredient, quantite: float) -> float:
    """
    Calcule la valeur d'un stock pour un ingrédient.
    
    ⚠️ ATTENTION : Pour les pièces, la quantité est en nombre de pièces,
    mais le prix est stocké en €/g. Il faut donc :
    - Convertir la quantité en grammes (quantité × poids_piece)
    - Multiplier par le prix en €/g
    
    OU de manière équivalente :
    - quantité × prix_unitaire × poids_piece
    
    Args:
        ingredient: L'objet Ingredient
        quantite: La quantité dans l'unité native
    
    Returns:
        float: La valeur en euros
    """
    if not ingredient or quantite <= 0:
        return 0
    
    prix = ingredient.prix_unitaire
    if not prix or prix <= 0:
        return 0
    
    if ingredient.unite == 'pièce':
        # Pour les pièces : quantité est en pièces, prix est en €/g
        # Valeur = nb_pieces × poids_piece × prix_par_gramme
        poids_piece = getattr(ingredient, 'poids_piece', None)
        if poids_piece and poids_piece > 0:
            return round(quantite * poids_piece * prix, 2)
        else:
            # Fallback si pas de poids_piece (ne devrait pas arriver)
            return round(quantite * prix, 2)
    else:
        # Pour g/ml : calcul direct
        return round(quantite * prix, 2)


def get_prix_unitaire_affichage(ingredient) -> tuple:
    """
    Retourne le prix unitaire et son unité d'affichage.
    
    Args:
        ingredient: L'objet Ingredient
    
    Returns:
        tuple: (prix_affichage, unite_affichage)
               ex: (15.50, "kg") pour un ingrédient à 0.0155€/g
               ex: (1.35, "pièce") pour une aubergine
    """
    if not ingredient or not ingredient.prix_unitaire or ingredient.prix_unitaire <= 0:
        return (0, None)
    
    prix = ingredient.prix_unitaire
    unite = ingredient.unite
    poids_piece = getattr(ingredient, 'poids_piece', None)
    
    if unite == 'pièce':
        if poids_piece and poids_piece > 0:
            return (prix * poids_piece, 'pièce')
        return (prix, 'pièce')
    elif unite == 'g':
        return (prix * 1000, 'kg')
    elif unite == 'ml':
        return (prix * 1000, 'L')
    else:
        return (prix, unite)
