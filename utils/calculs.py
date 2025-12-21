"""
utils/calculs.py
Fonctions de calcul centralisées pour l'application

Ce module regroupe les calculs répétés dans l'application :
- Calcul du budget de la liste de courses
- Calcul des totaux et statistiques
- Calcul des prix estimés

✅ FACTORISATION : Évite la duplication de code entre routes/courses.py et routes/api.py
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class BudgetResult:
    """Résultat du calcul de budget pour la liste de courses"""
    total_estime: float
    items_avec_prix: int
    items_sans_prix: int
    details: List[Dict[str, Any]]
    
    @property
    def total_items(self) -> int:
        """Nombre total d'items"""
        return self.items_avec_prix + self.items_sans_prix
    
    @property
    def pourcentage_avec_prix(self) -> float:
        """Pourcentage d'items ayant un prix"""
        if self.total_items == 0:
            return 0.0
        return (self.items_avec_prix / self.total_items) * 100
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire pour les templates ou l'API"""
        return {
            'total_estime': round(self.total_estime, 2),
            'items_avec_prix': self.items_avec_prix,
            'items_sans_prix': self.items_sans_prix,
            'total_items': self.total_items,
            'pourcentage_avec_prix': round(self.pourcentage_avec_prix, 1)
        }


def calculer_budget_courses(items: List[Any], include_details: bool = False) -> BudgetResult:
    """
    Calcule le budget estimé pour une liste de courses.
    
    Args:
        items: Liste d'objets ListeCourses (avec ingredient chargé via joinedload)
        include_details: Si True, inclut le détail par item dans le résultat
    
    Returns:
        BudgetResult contenant le total estimé et les statistiques
    
    Exemple d'utilisation:
        # Dans routes/courses.py
        from utils.calculs import calculer_budget_courses
        
        items = ListeCourses.query.options(joinedload(...)).filter_by(achete=False).all()
        budget = calculer_budget_courses(items)
        
        return render_template('courses.html',
            items=items,
            total_estime=budget.total_estime,
            items_avec_prix=budget.items_avec_prix,
            items_sans_prix=budget.items_sans_prix
        )
    """
    total_estime = 0.0
    items_avec_prix = 0
    items_sans_prix = 0
    details = []
    
    for item in items:
        prix_unitaire = getattr(item.ingredient, 'prix_unitaire', None) or 0
        quantite = getattr(item, 'quantite', 0) or 0
        
        if prix_unitaire > 0:
            prix_ligne = quantite * prix_unitaire
            total_estime += prix_ligne
            items_avec_prix += 1
        else:
            prix_ligne = 0
            items_sans_prix += 1
        
        if include_details:
            details.append({
                'id': item.id,
                'ingredient_id': item.ingredient_id,
                'ingredient_nom': item.ingredient.nom,
                'quantite': quantite,
                'unite': item.ingredient.unite,
                'prix_unitaire': prix_unitaire,
                'prix_estime': round(prix_ligne, 2)
            })
    
    return BudgetResult(
        total_estime=total_estime,
        items_avec_prix=items_avec_prix,
        items_sans_prix=items_sans_prix,
        details=details
    )


def calculer_prix_item(item: Any) -> float:
    """
    Calcule le prix estimé d'un seul item de la liste de courses.
    
    Args:
        item: Objet ListeCourses avec ingredient chargé
    
    Returns:
        Prix estimé (quantité × prix_unitaire), ou 0 si pas de prix
    """
    prix_unitaire = getattr(item.ingredient, 'prix_unitaire', None) or 0
    quantite = getattr(item, 'quantite', 0) or 0
    
    if prix_unitaire > 0:
        return quantite * prix_unitaire
    return 0.0


def calculer_valeur_stock(stocks: List[Any]) -> Dict[str, Any]:
    """
    Calcule la valeur totale du stock du frigo.
    
    Args:
        stocks: Liste d'objets StockFrigo (avec ingredient chargé)
    
    Returns:
        Dictionnaire avec la valeur totale et les statistiques
    """
    valeur_totale = 0.0
    items_avec_prix = 0
    items_sans_prix = 0
    
    for stock in stocks:
        prix_unitaire = getattr(stock.ingredient, 'prix_unitaire', None) or 0
        quantite = getattr(stock, 'quantite', 0) or 0
        
        if prix_unitaire > 0:
            valeur_totale += quantite * prix_unitaire
            items_avec_prix += 1
        else:
            items_sans_prix += 1
    
    return {
        'valeur_totale': round(valeur_totale, 2),
        'items_avec_prix': items_avec_prix,
        'items_sans_prix': items_sans_prix,
        'total_items': items_avec_prix + items_sans_prix
    }


def formater_prix(montant: float, devise: str = '€') -> str:
    """
    Formate un montant en prix lisible.
    
    Args:
        montant: Montant à formater
        devise: Symbole de la devise (défaut: €)
    
    Returns:
        Chaîne formatée (ex: "12.50 €")
    """
    if montant <= 0:
        return f"0.00 {devise}"
    return f"{montant:.2f} {devise}"


def calculer_cout_recette_items(ingredients_recette: List[Any]) -> float:
    """
    Calcule le coût total d'une liste d'ingrédients de recette.
    
    Args:
        ingredients_recette: Liste d'objets IngredientRecette (avec ingredient chargé)
    
    Returns:
        Coût total estimé
    """
    cout_total = 0.0
    
    for ing_rec in ingredients_recette:
        prix_unitaire = getattr(ing_rec.ingredient, 'prix_unitaire', None) or 0
        quantite = getattr(ing_rec, 'quantite', 0) or 0
        
        if prix_unitaire > 0:
            cout_total += quantite * prix_unitaire
    
    return round(cout_total, 2)
