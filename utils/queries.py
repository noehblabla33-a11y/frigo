"""
utils/queries.py
Requêtes SQL centralisées et optimisées

Ce module centralise les requêtes complexes réutilisées dans plusieurs routes,
garantissant des performances optimales (pas de N+1) et une maintenance simplifiée.
"""

from sqlalchemy.orm import joinedload
from sqlalchemy import func, desc
from models.models import (
    db, Ingredient, StockFrigo, Recette, 
    IngredientRecette, RecettePlanifiee, ListeCourses
)
from typing import List, Dict, Optional
from datetime import datetime, timedelta


# ============================================
# REQUÊTES LISTE DE COURSES
# ============================================

def get_courses_non_achetees() -> List[ListeCourses]:
    """
    Retourne les items de la liste de courses non achetés.
    Ingrédients préchargés pour éviter N+1.
    
    Returns:
        Liste de ListeCourses avec ingrédients préchargés
    """
    return ListeCourses.query.options(
        joinedload(ListeCourses.ingredient)
    ).filter_by(achete=False).all()


def get_historique_courses(limit: int = 10) -> List[ListeCourses]:
    """
    Retourne l'historique des courses achetées.
    
    Args:
        limit: Nombre maximum d'items à retourner
    
    Returns:
        Liste de ListeCourses triée par id décroissant
    """
    return ListeCourses.query.options(
        joinedload(ListeCourses.ingredient)
    ).filter_by(achete=True)\
     .order_by(desc(ListeCourses.id))\
     .limit(limit)\
     .all()


def get_course_by_ingredient(ingredient_id: int, achete: bool = False) -> Optional[ListeCourses]:
    """
    Recherche un item de courses par ingrédient.
    
    Args:
        ingredient_id: ID de l'ingrédient
        achete: Statut d'achat
    
    Returns:
        ListeCourses ou None
    """
    return ListeCourses.query.filter_by(
        ingredient_id=ingredient_id,
        achete=achete
    ).first()


# ============================================
# REQUÊTES RECETTES
# ============================================

def get_recettes_avec_ingredients() -> List[Recette]:
    """
    Retourne toutes les recettes avec leurs ingrédients préchargés.
    
    Returns:
        Liste de recettes optimisée
    """
    return Recette.query.options(
        joinedload(Recette.ingredients)
            .joinedload(IngredientRecette.ingredient)
    ).order_by(Recette.nom).all()


def get_recette_complete(recette_id: int) -> Optional[Recette]:
    """
    Retourne une recette avec toutes ses relations préchargées.
    
    Args:
        recette_id: ID de la recette
    
    Returns:
        Recette complète ou None
    """
    return Recette.query.options(
        joinedload(Recette.ingredients)
            .joinedload(IngredientRecette.ingredient),
        joinedload(Recette.etapes),
        joinedload(Recette.planifications)
    ).get(recette_id)


def get_recettes_par_type(type_recette: str) -> List[Recette]:
    """
    Retourne les recettes d'un type donné.
    
    Args:
        type_recette: Type de recette
    
    Returns:
        Liste de recettes
    """
    return Recette.query.options(
        joinedload(Recette.ingredients)
    ).filter_by(type_recette=type_recette).all()


def get_recettes_avec_ingredient(ingredient_id: int) -> List[Recette]:
    """
    Retourne les recettes contenant un ingrédient donné.
    
    Args:
        ingredient_id: ID de l'ingrédient
    
    Returns:
        Liste de recettes
    """
    return Recette.query.options(
        joinedload(Recette.ingredients)
            .joinedload(IngredientRecette.ingredient)
    ).join(IngredientRecette)\
     .filter(IngredientRecette.ingredient_id == ingredient_id)\
     .all()


# ============================================
# REQUÊTES PLANIFICATION
# ============================================

def get_recettes_planifiees(preparee: bool = False) -> List[RecettePlanifiee]:
    """
    Retourne les recettes planifiées.
    
    Args:
        preparee: Filtre sur le statut préparé
    
    Returns:
        Liste de RecettePlanifiee avec recettes préchargées
    """
    return RecettePlanifiee.query.options(
        joinedload(RecettePlanifiee.recette_ref)
            .joinedload(Recette.ingredients)
            .joinedload(IngredientRecette.ingredient)
    ).filter_by(preparee=preparee)\
     .order_by(RecettePlanifiee.date_planification)\
     .all()


def get_historique_preparations(limit: int = 50) -> List[RecettePlanifiee]:
    """
    Retourne l'historique des recettes préparées.
    
    Args:
        limit: Nombre maximum d'items
    
    Returns:
        Liste de RecettePlanifiee triée par date de préparation
    """
    return RecettePlanifiee.query.options(
        joinedload(RecettePlanifiee.recette_ref)
    ).filter_by(preparee=True)\
     .order_by(desc(RecettePlanifiee.date_preparation))\
     .limit(limit)\
     .all()


def get_preparations_periode(date_debut: datetime, date_fin: datetime = None) -> List[RecettePlanifiee]:
    """
    Retourne les préparations sur une période donnée.
    
    Args:
        date_debut: Date de début
        date_fin: Date de fin (défaut: maintenant)
    
    Returns:
        Liste de RecettePlanifiee
    """
    if date_fin is None:
        date_fin = datetime.utcnow()
    
    return RecettePlanifiee.query.options(
        joinedload(RecettePlanifiee.recette_ref)
            .joinedload(Recette.ingredients)
            .joinedload(IngredientRecette.ingredient)
    ).filter(
        RecettePlanifiee.preparee == True,
        RecettePlanifiee.date_preparation >= date_debut,
        RecettePlanifiee.date_preparation <= date_fin
    ).order_by(RecettePlanifiee.date_preparation).all()


# ============================================
# REQUÊTES INGRÉDIENTS
# ============================================

def get_ingredients_avec_stock() -> List[Ingredient]:
    """
    Retourne tous les ingrédients avec leur stock préchargé.
    
    Returns:
        Liste d'ingrédients avec stock
    """
    return Ingredient.query.options(
        joinedload(Ingredient.stock)
    ).order_by(Ingredient.nom).all()


def get_ingredients_en_stock() -> List[Ingredient]:
    """
    Retourne uniquement les ingrédients en stock.
    
    Returns:
        Liste d'ingrédients avec quantité > 0
    """
    return Ingredient.query.join(StockFrigo)\
        .filter(StockFrigo.quantite > 0)\
        .order_by(Ingredient.nom).all()


def get_categories_count() -> Dict[str, int]:
    """
    Compte le nombre d'ingrédients par catégorie.
    Optimisé en une seule requête.
    
    Returns:
        Dict {categorie: count}
    """
    results = db.session.query(
        Ingredient.categorie,
        func.count(Ingredient.id)
    ).group_by(Ingredient.categorie).all()
    
    return {cat: count for cat, count in results if cat}


# ============================================
# REQUÊTES STATISTIQUES
# ============================================

def get_top_recettes(limit: int = 10) -> List[Dict]:
    """
    Retourne les recettes les plus préparées.
    
    Args:
        limit: Nombre de recettes à retourner
    
    Returns:
        Liste de dicts {recette: Recette, nb_preparations: int}
    """
    results = db.session.query(
        Recette,
        func.count(RecettePlanifiee.id).label('nb_preparations')
    ).join(RecettePlanifiee, Recette.id == RecettePlanifiee.recette_id)\
     .filter(RecettePlanifiee.preparee == True)\
     .group_by(Recette.id)\
     .order_by(desc('nb_preparations'))\
     .limit(limit)\
     .all()
    
    return [{'recette': r, 'nb_preparations': count} for r, count in results]


def get_ingredients_plus_utilises(limit: int = 10) -> List[Dict]:
    """
    Retourne les ingrédients les plus utilisés dans les recettes préparées.
    
    Args:
        limit: Nombre d'ingrédients à retourner
    
    Returns:
        Liste de dicts {ingredient: Ingredient, count: int}
    """
    results = db.session.query(
        Ingredient,
        func.count(IngredientRecette.id).label('usage_count')
    ).select_from(RecettePlanifiee)\
     .join(Recette, RecettePlanifiee.recette_id == Recette.id)\
     .join(IngredientRecette, Recette.id == IngredientRecette.recette_id)\
     .join(Ingredient, IngredientRecette.ingredient_id == Ingredient.id)\
     .filter(RecettePlanifiee.preparee == True)\
     .group_by(Ingredient.id)\
     .order_by(desc('usage_count'))\
     .limit(limit)\
     .all()
    
    return [{'ingredient': ing, 'count': count} for ing, count in results]


def get_stats_periode(jours: int = 30) -> Dict:
    """
    Calcule les statistiques sur une période donnée.
    
    Args:
        jours: Nombre de jours en arrière
    
    Returns:
        Dict avec statistiques
    """
    date_limite = datetime.utcnow() - timedelta(days=jours)
    
    # Nombre de recettes préparées
    nb_recettes = RecettePlanifiee.query.filter(
        RecettePlanifiee.preparee == True,
        RecettePlanifiee.date_preparation >= date_limite
    ).count()
    
    # Coût total estimé
    preparations = get_preparations_periode(date_limite)
    cout_total = sum(p.recette_ref.calculer_cout() for p in preparations)
    
    return {
        'nb_recettes': nb_recettes,
        'cout_total': round(cout_total, 2),
        'cout_moyen': round(cout_total / nb_recettes, 2) if nb_recettes > 0 else 0,
        'periode_jours': jours
    }
