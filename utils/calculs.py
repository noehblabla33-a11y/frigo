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
    
    ⚠️ ATTENTION : Pour les pièces, le prix est stocké en €/g !
    Il faut donc multiplier par poids_piece pour obtenir le prix correct.
    
    Args:
        item: Un objet ListeCourses avec ingredient préchargé
    
    Returns:
        float: Le prix total pour cet item
    """
    if not item or not item.ingredient:
        return 0
    
    ing = item.ingredient
    if not ing.prix_unitaire or ing.prix_unitaire <= 0:
        return 0
    
    if ing.unite == 'pièce' and ing.poids_piece and ing.poids_piece > 0:
        # Pour les pièces : quantité × poids_piece × prix_par_gramme
        return round(item.quantite * ing.poids_piece * ing.prix_unitaire, 2)
    else:
        # Pour g/ml : calcul direct
        return round(item.quantite * ing.prix_unitaire, 2)


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
    
    Args:
        recette: Un objet Recette avec ingredients préchargés
    
    Returns:
        float: Le coût total de la recette
    """
    if not recette or not recette.ingredients:
        return 0
    
    cout_total = 0
    for ing_rec in recette.ingredients:
        ing = ing_rec.ingredient
        if not ing.prix_unitaire or ing.prix_unitaire <= 0:
            continue
            
        if ing.unite == 'pièce' and ing.poids_piece and ing.poids_piece > 0:
            cout_total += ing_rec.quantite * ing.poids_piece * ing.prix_unitaire
        else:
            cout_total += ing_rec.quantite * ing.prix_unitaire
    
    return round(cout_total, 2)
