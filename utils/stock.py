"""
utils/stock.py
Fonctions centralisées pour la gestion du stock du frigo

Ce module regroupe toutes les opérations CRUD sur le stock,
évitant la duplication de code entre frigo.py, courses.py et autres.
"""

from models.models import db, StockFrigo, Ingredient
from typing import Optional, Tuple


def get_stock(ingredient_id: int) -> Optional[StockFrigo]:
    """
    Récupère le stock d'un ingrédient.
    
    Args:
        ingredient_id: ID de l'ingrédient
    
    Returns:
        StockFrigo ou None si pas en stock
    """
    return StockFrigo.query.filter_by(ingredient_id=ingredient_id).first()


def ajouter_au_stock(ingredient_id: int, quantite: float) -> Tuple[StockFrigo, float]:
    """
    Ajoute une quantité au stock d'un ingrédient.
    Crée l'entrée si elle n'existe pas.
    
    Args:
        ingredient_id: ID de l'ingrédient
        quantite: Quantité à ajouter (en unité native)
    
    Returns:
        Tuple (StockFrigo, nouvelle_quantite)
    
    Example:
        stock, new_qty = ajouter_au_stock(ingredient_id=5, quantite=250)
    """
    stock = get_stock(ingredient_id)
    
    if stock:
        stock.quantite += quantite
        nouvelle_quantite = stock.quantite
    else:
        stock = StockFrigo(ingredient_id=ingredient_id, quantite=quantite)
        db.session.add(stock)
        nouvelle_quantite = quantite
    
    return stock, nouvelle_quantite


def retirer_du_stock(ingredient_id: int, quantite: float) -> Tuple[Optional[StockFrigo], float]:
    """
    Retire une quantité du stock (minimum 0).
    
    Args:
        ingredient_id: ID de l'ingrédient
        quantite: Quantité à retirer (en unité native)
    
    Returns:
        Tuple (StockFrigo ou None, quantité restante)
        Retourne (None, 0) si l'ingrédient n'est pas en stock
    
    Example:
        stock, remaining = retirer_du_stock(ingredient_id=5, quantite=100)
    """
    stock = get_stock(ingredient_id)
    
    if stock:
        stock.quantite = max(0, stock.quantite - quantite)
        return stock, stock.quantite
    
    return None, 0


def definir_stock(ingredient_id: int, quantite: float) -> Optional[StockFrigo]:
    """
    Définit la quantité exacte en stock.
    Supprime l'entrée si quantité <= 0.
    
    Args:
        ingredient_id: ID de l'ingrédient
        quantite: Quantité à définir (en unité native)
    
    Returns:
        StockFrigo ou None si supprimé
    
    Example:
        stock = definir_stock(ingredient_id=5, quantite=500)
    """
    stock = get_stock(ingredient_id)
    
    if stock:
        if quantite <= 0:
            db.session.delete(stock)
            return None
        stock.quantite = quantite
        return stock
    else:
        if quantite > 0:
            stock = StockFrigo(ingredient_id=ingredient_id, quantite=quantite)
            db.session.add(stock)
            return stock
    
    return None


def supprimer_du_frigo(ingredient_id: int) -> bool:
    """
    Supprime complètement un ingrédient du frigo.
    
    Args:
        ingredient_id: ID de l'ingrédient
    
    Returns:
        True si supprimé, False si pas trouvé
    """
    stock = get_stock(ingredient_id)
    
    if stock:
        db.session.delete(stock)
        return True
    
    return False


def transferer_vers_stock(items_achetes: list) -> dict:
    """
    Transfère des items achetés vers le stock du frigo.
    Utilisé typiquement lors de la validation des courses.
    
    Args:
        items_achetes: Liste de dicts avec 'ingredient_id' et 'quantite'
    
    Returns:
        Dict avec statistiques: {'transferes': int, 'erreurs': list}
    
    Example:
        result = transferer_vers_stock([
            {'ingredient_id': 1, 'quantite': 500},
            {'ingredient_id': 2, 'quantite': 2}
        ])
    """
    transferes = 0
    erreurs = []
    
    for item in items_achetes:
        try:
            ingredient_id = item.get('ingredient_id')
            quantite = item.get('quantite', 0)
            
            if ingredient_id and quantite > 0:
                ajouter_au_stock(ingredient_id, quantite)
                transferes += 1
        except Exception as e:
            erreurs.append(f"Erreur transfert ID {item.get('ingredient_id')}: {str(e)}")
    
    return {
        'transferes': transferes,
        'erreurs': erreurs
    }


def get_quantite_disponible(ingredient_id: int) -> float:
    """
    Retourne la quantité disponible pour un ingrédient.
    
    Args:
        ingredient_id: ID de l'ingrédient
    
    Returns:
        Quantité en stock (0 si pas en stock)
    """
    stock = get_stock(ingredient_id)
    return stock.quantite if stock else 0


def verifier_disponibilite(ingredient_id: int, quantite_requise: float) -> Tuple[bool, float]:
    """
    Vérifie si une quantité est disponible en stock.
    
    Args:
        ingredient_id: ID de l'ingrédient
        quantite_requise: Quantité nécessaire
    
    Returns:
        Tuple (disponible: bool, quantite_manquante: float)
    
    Example:
        disponible, manquant = verifier_disponibilite(5, 200)
        if not disponible:
            print(f"Il manque {manquant} unités")
    """
    disponible = get_quantite_disponible(ingredient_id)
    
    if disponible >= quantite_requise:
        return True, 0
    
    return False, quantite_requise - disponible


def get_stocks_avec_ingredients(order_by='nom'):
    """
    Récupère tous les stocks avec les ingrédients préchargés.
    Optimisé pour éviter les requêtes N+1.
    
    Args:
        order_by: Champ de tri ('nom', 'quantite', 'date_modification')
    
    Returns:
        Liste de StockFrigo avec ingrédients préchargés
    """
    from sqlalchemy.orm import joinedload
    
    query = StockFrigo.query.options(
        joinedload(StockFrigo.ingredient)
    ).join(StockFrigo.ingredient)
    
    if order_by == 'nom':
        query = query.order_by(Ingredient.nom)
    elif order_by == 'quantite':
        query = query.order_by(StockFrigo.quantite.desc())
    elif order_by == 'date_modification':
        query = query.order_by(StockFrigo.date_modification.desc())
    
    return query.all()


def vider_frigo() -> int:
    """
    Vide complètement le frigo.
    
    Returns:
        Nombre d'items supprimés
    """
    count = StockFrigo.query.count()
    StockFrigo.query.delete()
    return count
