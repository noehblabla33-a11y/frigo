from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class BudgetResult:
    """
    Résultat du calcul de budget pour une liste de courses.
    """
    total_estime: float = 0
    items_avec_prix: int = 0
    items_sans_prix: int = 0
    details: List[dict] = field(default_factory=list)


def calculer_prix_item(item) -> float:
    """
    Calcule le prix total d'un item de la liste de courses.

    Paramètres:
        item: Un objet ListeCourses avec ingredient préchargé

    Retour:
        float: Le prix total pour cet item
    """
    if not item or not item.ingredient:
        return 0

    return item.ingredient.calculer_prix(item.quantite)


def calculer_budget_courses(items, include_details: bool = False) -> BudgetResult:
    """
    Calcule le budget total d'une liste de courses.
    
    Args:
        items: Liste d'objets ListeCourses avec ingredients préchargés
        include_details: Si True, inclut les détails de chaque item
    
    Returns:
        BudgetResult: Objet contenant le total et les statistiques
    """
    result = BudgetResult()
    
    if not items:
        return result
    
    for item in items:
        if not item.ingredient:
            result.items_sans_prix += 1
            continue
        
        ing = item.ingredient
        prix_unitaire = ing.prix_unitaire
        
        if prix_unitaire and prix_unitaire > 0:
            # Utiliser la fonction centralisée
            prix_total = calculer_prix_item(item)
            result.total_estime += prix_total
            result.items_avec_prix += 1
            
            if include_details:
                result.details.append({
                    'id': item.id,
                    'ingredient_id': ing.id,
                    'ingredient_nom': ing.nom,
                    'quantite': item.quantite,
                    'unite': ing.unite,
                    'prix_unitaire': prix_unitaire,
                    'prix_total': round(prix_total, 2)
                })
        else:
            result.items_sans_prix += 1
            
            if include_details:
                result.details.append({
                    'id': item.id,
                    'ingredient_id': ing.id,
                    'ingredient_nom': ing.nom,
                    'quantite': item.quantite,
                    'unite': ing.unite,
                    'prix_unitaire': 0,
                    'prix_total': 0
                })
    
    result.total_estime = round(result.total_estime, 2)
    return result


def calculer_cout_recette(recette) -> float:
    """
    Calcule le coût total d'une recette.

    Paramètres:
        recette: Un objet Recette avec ingredients préchargés

    Retour:
        float: Le coût total de la recette
    """
    if not recette or not recette.ingredients:
        return 0

    return round(sum(
        ing_rec.ingredient.calculer_prix(ing_rec.quantite)
        for ing_rec in recette.ingredients
    ), 2)

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

    Paramètres:
        ingredient: L'objet Ingredient
        quantite: La quantité dans l'unité native

    Retour:
        float: La valeur en euros
    """
    if not ingredient or quantite <= 0:
        return 0

    return ingredient.calculer_prix(quantite)


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
