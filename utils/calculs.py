"""
utils/calculs.py
Fonctions de calcul centralisées pour les prix et budgets

⚠️ IMPORTANT - SYSTÈME DE STOCKAGE DES PRIX :
Le prix est TOUJOURS stocké en €/g (ou €/ml), même pour les pièces !
Pour les pièces avec poids_piece défini :
- prix_unitaire = prix_par_piece / poids_piece (stocké en €/g)
- valeur_stock = quantité × poids_piece × prix_unitaire

✅ CORRIGÉ : Calcul correct pour les ingrédients en pièce
"""
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
