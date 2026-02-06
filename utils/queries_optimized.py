from sqlalchemy.orm import joinedload, selectinload, contains_eager
from sqlalchemy import func, desc, and_, or_
from models.models import (
    db, Ingredient, StockFrigo, Recette, IngredientRecette,
    RecettePlanifiee, ListeCourses, EtapeRecette, IngredientSaison
)
from datetime import datetime, timedelta
from typing import List, Dict, Optional

# ============================================
# STOCK / FRIGO
# ============================================

def get_stocks_with_ingredients(order_by='nom', filter_empty=True):
    """
    Récupère tous les stocks avec leurs ingrédients préchargés.
    
    Args:
        order_by: 'nom', 'date', 'quantite', 'categorie'
        filter_empty: Exclure les stocks à 0
    
    Returns:
        Liste de StockFrigo avec ingredient préchargé
    
    Requêtes: 1 (au lieu de N+1)
    """
    query = StockFrigo.query.options(
        joinedload(StockFrigo.ingredient).joinedload(Ingredient.saisons)
    )
    
    if filter_empty:
        query = query.filter(StockFrigo.quantite > 0)
    
    # Tri
    if order_by == 'nom':
        query = query.join(Ingredient).order_by(Ingredient.nom)
    elif order_by == 'date':
        query = query.order_by(desc(StockFrigo.date_modification))
    elif order_by == 'quantite':
        query = query.order_by(desc(StockFrigo.quantite))
    elif order_by == 'categorie':
        query = query.join(Ingredient).order_by(Ingredient.categorie, Ingredient.nom)
    
    return query.all()


def get_stock_by_ingredient_id(ingredient_id):
    """
    Récupère le stock d'un ingrédient spécifique.
    
    Args:
        ingredient_id: ID de l'ingrédient
    
    Returns:
        StockFrigo ou None
    """
    return StockFrigo.query.options(
        joinedload(StockFrigo.ingredient)
    ).filter_by(ingredient_id=ingredient_id).first()


def get_stocks_low(threshold_map=None):
    """
    Récupère les stocks bas selon des seuils par unité.
    
    Args:
        threshold_map: Dict {unite: seuil} ex: {'g': 100, 'ml': 200, 'pièce': 2}
    
    Returns:
        Liste de StockFrigo sous les seuils
    """
    if threshold_map is None:
        threshold_map = {'g': 100, 'ml': 250, 'pièce': 2}
    
    stocks = get_stocks_with_ingredients(filter_empty=True)
    
    low_stocks = []
    for stock in stocks:
        seuil = threshold_map.get(stock.ingredient.unite, 100)
        if stock.quantite < seuil:
            low_stocks.append(stock)
    
    return low_stocks


# ============================================
# INGRÉDIENTS
# ============================================

def get_all_ingredients(with_stock=False, with_saisons=True):
    """
    Récupère tous les ingrédients avec relations préchargées.
    
    Args:
        with_stock: Inclure les infos de stock
        with_saisons: Inclure les saisons
    
    Returns:
        Liste d'Ingredient
    """
    query = Ingredient.query
    
    options = []
    if with_saisons:
        options.append(joinedload(Ingredient.saisons))
    if with_stock:
        options.append(joinedload(Ingredient.stock))
    
    if options:
        query = query.options(*options)
    
    return query.order_by(Ingredient.nom).all()


def get_ingredients_by_category(category):
    """
    Récupère les ingrédients d'une catégorie.
    
    Args:
        category: Nom de la catégorie
    
    Returns:
        Liste d'Ingredient
    """
    return Ingredient.query.options(
        joinedload(Ingredient.saisons),
        joinedload(Ingredient.stock)
    ).filter_by(categorie=category).order_by(Ingredient.nom).all()


def get_ingredients_in_stock():
    """
    Récupère uniquement les ingrédients qui sont en stock.
    
    Returns:
        Liste d'Ingredient avec stock > 0
    """
    return Ingredient.query.options(
        joinedload(Ingredient.stock),
        joinedload(Ingredient.saisons)
    ).join(StockFrigo).filter(
        StockFrigo.quantite > 0
    ).order_by(Ingredient.nom).all()


def get_ingredients_de_saison(saison=None):
    """
    Récupère les ingrédients de saison.
    
    Args:
        saison: Saison à filtrer (défaut: saison actuelle)
    
    Returns:
        Liste d'Ingredient de saison ou disponibles toute l'année
    """
    from utils.saisons import get_saison_actuelle
    
    if saison is None:
        saison = get_saison_actuelle()
    
    # Ingrédients avec cette saison
    ingredients_saison = db.session.query(Ingredient.id).join(
        IngredientSaison
    ).filter(IngredientSaison.saison == saison).subquery()
    
    # Ingrédients sans saison définie (toute l'année)
    ingredients_sans_saison = db.session.query(Ingredient.id).outerjoin(
        IngredientSaison
    ).filter(IngredientSaison.id.is_(None)).subquery()
    
    return Ingredient.query.options(
        joinedload(Ingredient.saisons),
        joinedload(Ingredient.stock)
    ).filter(
        or_(
            Ingredient.id.in_(ingredients_saison),
            Ingredient.id.in_(ingredients_sans_saison)
        )
    ).order_by(Ingredient.nom).all()


# ============================================
# RECETTES
# ============================================

def get_recettes_with_all_relations(limit=None):
    """
    Récupère les recettes avec TOUTES les relations préchargées.
    
    Optimal pour les pages de liste ou recommandations.
    
    Args:
        limit: Nombre max de recettes
    
    Returns:
        Liste de Recette avec tout préchargé
    
    Requêtes: 3 max (recettes, ingredients, etapes)
    """
    query = Recette.query.options(
        # Précharger les ingrédients avec leur relation ingredient
        selectinload(Recette.ingredients).joinedload(IngredientRecette.ingredient),
        # Précharger les étapes
        selectinload(Recette.etapes)
    ).order_by(Recette.nom)
    
    if limit:
        query = query.limit(limit)
    
    return query.all()

def get_recettes_avec_ingredient(ingredient_id: int) -> List[Recette]:
    """
    Retourne les recettes contenant un ingrédient donné.

    Paramètres:
        ingredient_id: ID de l'ingrédient

    Retour:
        Liste de Recette
    """
    return Recette.query.options(
        selectinload(Recette.ingredients).joinedload(IngredientRecette.ingredient)
    ).join(IngredientRecette)\
     .filter(IngredientRecette.ingredient_id == ingredient_id)\
     .order_by(Recette.nom)\
     .all()

def get_recette_with_details(recette_id):
    """
    Récupère une recette avec tous ses détails.
    
    Args:
        recette_id: ID de la recette
    
    Returns:
        Recette avec tout préchargé ou None
    """
    return Recette.query.options(
        joinedload(Recette.ingredients).joinedload(IngredientRecette.ingredient).joinedload(Ingredient.saisons),
        joinedload(Recette.ingredients).joinedload(IngredientRecette.ingredient).joinedload(Ingredient.stock),
        selectinload(Recette.etapes),
        selectinload(Recette.planifications)
    ).get(recette_id)


def get_recettes_by_type(type_recette, with_ingredients=True):
    """
    Récupère les recettes d'un type spécifique.
    
    Args:
        type_recette: Type de recette
        with_ingredients: Précharger les ingrédients
    
    Returns:
        Liste de Recette
    """
    query = Recette.query.filter_by(type_recette=type_recette)
    
    if with_ingredients:
        query = query.options(
            selectinload(Recette.ingredients).joinedload(IngredientRecette.ingredient)
        )
    
    return query.order_by(Recette.nom).all()


def get_recettes_realisables():
    """
    Récupère les recettes réalisables avec le stock actuel.
    
    Returns:
        Liste de Recette dont tous les ingrédients sont en stock
    """
    recettes = get_recettes_with_all_relations()
    
    realisables = []
    for recette in recettes:
        disponibilite = recette.calculer_disponibilite_ingredients()
        if disponibilite['realisable']:
            realisables.append(recette)
    
    return realisables


def search_recettes(search_query, type_filter=None, ingredient_id=None):
    """
    Recherche de recettes avec filtres multiples.
    
    Args:
        search_query: Terme de recherche
        type_filter: Filtrer par type
        ingredient_id: Filtrer par ingrédient
    
    Returns:
        Liste de Recette
    """
    query = Recette.query.options(
        selectinload(Recette.ingredients).joinedload(IngredientRecette.ingredient)
    )
    
    if search_query:
        query = query.filter(Recette.nom.ilike(f'%{search_query}%'))
    
    if type_filter:
        query = query.filter(Recette.type_recette == type_filter)
    
    if ingredient_id:
        query = query.join(IngredientRecette).filter(
            IngredientRecette.ingredient_id == ingredient_id
        )
    
    return query.order_by(Recette.nom).all()


# ============================================
# PLANIFICATION
# ============================================

def get_planifications_pending():
    """
    Récupère les recettes planifiées non préparées.
    
    Returns:
        Liste de RecettePlanifiee avec recette préchargée
    """
    return RecettePlanifiee.query.options(
        joinedload(RecettePlanifiee.recette_ref).selectinload(Recette.ingredients).joinedload(IngredientRecette.ingredient)
    ).filter_by(preparee=False).order_by(RecettePlanifiee.date_planification).all()


def get_planifications_historique(limit=50):
    """
    Récupère l'historique des recettes préparées.
    
    Args:
        limit: Nombre max de résultats
    
    Returns:
        Liste de RecettePlanifiee
    """
    return RecettePlanifiee.query.options(
        joinedload(RecettePlanifiee.recette_ref)
    ).filter_by(preparee=True).order_by(
        desc(RecettePlanifiee.date_preparation)
    ).limit(limit).all()


# ============================================
# COURSES
# ============================================

def get_courses_non_achetees():
    """
    Récupère la liste de courses non achetée, en excluant les items orphelins.

    Retour:
        Liste de ListeCourses avec ingredient et saisons préchargés
    """
    return ListeCourses.query\
        .join(Ingredient, ListeCourses.ingredient_id == Ingredient.id)\
        .options(joinedload(ListeCourses.ingredient).joinedload(Ingredient.saisons))\
        .filter(ListeCourses.achete == False)\
        .order_by(ListeCourses.id)\
        .all()


def nettoyer_courses_orphelines() -> int:
    """
    Supprime les items de la liste de courses dont l'ingrédient n'existe plus.

    Retour:
        int: Nombre d'items supprimés
    """
    orphelins = ListeCourses.query\
        .outerjoin(Ingredient, ListeCourses.ingredient_id == Ingredient.id)\
        .filter(Ingredient.id == None)\
        .all()

    count = len(orphelins)
    for item in orphelins:
        db.session.delete(item)

    if count > 0:
        db.session.commit()

    return count

def get_historique_courses(limit: int = 10) -> List[ListeCourses]:
    """
    Retourne l'historique des courses achetées.

    Paramètres:
        limit: Nombre maximum d'items à retourner

    Retour:
        Liste de ListeCourses triée par id décroissant
    """
    return ListeCourses.query\
        .join(Ingredient, ListeCourses.ingredient_id == Ingredient.id)\
        .options(joinedload(ListeCourses.ingredient))\
        .filter(ListeCourses.achete == True)\
        .order_by(desc(ListeCourses.id))\
        .limit(limit)\
        .all()


def get_preparations_periode(date_debut: datetime, date_fin: datetime = None) -> List[RecettePlanifiee]:
    """
    Retourne les préparations sur une période donnée.

    Paramètres:
        date_debut: Date de début
        date_fin: Date de fin (défaut: maintenant)

    Retour:
        Liste de RecettePlanifiee
    """
    if date_fin is None:
        date_fin = datetime.utcnow()

    return RecettePlanifiee.query.options(
        joinedload(RecettePlanifiee.recette_ref)
            .selectinload(Recette.ingredients)
            .joinedload(IngredientRecette.ingredient)
    ).filter(
        RecettePlanifiee.preparee == True,
        RecettePlanifiee.date_preparation >= date_debut,
        RecettePlanifiee.date_preparation <= date_fin
    ).order_by(RecettePlanifiee.date_preparation).all()

def get_courses_by_category():
    """
    Récupère la liste de courses groupée par catégorie.
    
    Returns:
        Dict {categorie: [ListeCourses]}
    """
    items = get_courses_non_achetees()
    
    by_category = {}
    for item in items:
        cat = item.ingredient.categorie or 'Autres'
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(item)
    
    return by_category


def get_course_by_ingredient(ingredient_id: int, achete: bool = False) -> Optional[ListeCourses]:
    """
    Recherche un item de courses par ingrédient.

    Paramètres:
        ingredient_id: ID de l'ingrédient
        achete: Statut d'achat (défaut: False)

    Retour:
        ListeCourses avec ingrédient préchargé ou None
    """
    return ListeCourses.query\
        .options(joinedload(ListeCourses.ingredient))\
        .filter_by(ingredient_id=ingredient_id, achete=achete)\
        .first()


# ============================================
# STATISTIQUES (REQUÊTES AGRÉGÉES)
# ============================================

def get_top_recettes(limit: int = 10) -> List[Dict]:
    """
    Retourne les recettes les plus préparées.

    Paramètres:
        limit: Nombre de recettes à retourner

    Retour:
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

    Paramètres:
        limit: Nombre d'ingrédients à retourner

    Retour:
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

    Paramètres:
        jours: Nombre de jours en arrière

    Retour:
        Dict avec nb_recettes, cout_total, cout_moyen, periode_jours
    """
    date_limite = datetime.utcnow() - timedelta(days=jours)

    nb_recettes = RecettePlanifiee.query.filter(
        RecettePlanifiee.preparee == True,
        RecettePlanifiee.date_preparation >= date_limite
    ).count()

    preparations = get_preparations_periode(date_limite)
    cout_total = sum(p.recette_ref.calculer_cout() for p in preparations)

    return {
        'nb_recettes': nb_recettes,
        'cout_total': round(cout_total, 2),
        'cout_moyen': round(cout_total / nb_recettes, 2) if nb_recettes > 0 else 0,
        'periode_jours': jours
    }

def get_categories_count():
    """
    Compte les ingrédients par catégorie.
    
    Returns:
        Dict {categorie: count}
    
    Requêtes: 1
    """
    result = db.session.query(
        func.coalesce(Ingredient.categorie, 'Autres').label('categorie'),
        func.count(Ingredient.id).label('count')
    ).group_by(Ingredient.categorie).all()
    
    return {row.categorie: row.count for row in result}


def get_stock_stats():
    """
    Calcule les statistiques du stock.

    Retour:
        Dict avec nb_items, valeur_totale, par_categorie
    """
    stocks = get_stocks_with_ingredients()

    total_value = sum(
        stock.ingredient.calculer_prix(stock.quantite)
        for stock in stocks
    )

    by_category = {}
    for stock in stocks:
        cat = stock.ingredient.categorie or 'Autres'
        by_category[cat] = by_category.get(cat, 0) + 1

    return {
        'nb_items': len(stocks),
        'valeur_totale': round(total_value, 2),
        'par_categorie': by_category
    }


def get_recettes_stats():
    """
    Calcule les statistiques des recettes.
    
    Returns:
        Dict avec total, par_type, realisables
    """
    # Total et par type
    total = Recette.query.count()
    
    by_type = db.session.query(
        Recette.type_recette,
        func.count(Recette.id)
    ).group_by(Recette.type_recette).all()
    
    # Planifiées non préparées
    planifiees = RecettePlanifiee.query.filter_by(preparee=False).count()
    
    return {
        'total': total,
        'par_type': {t or 'Non classé': c for t, c in by_type},
        'planifiees': planifiees
    }


# ============================================
# BONNES PRATIQUES - DOCUMENTATION
# ============================================

"""
GUIDE D'OPTIMISATION DES REQUÊTES SQLAlchemy
============================================

1. TOUJOURS utiliser eager loading pour les relations accédées :
   
   # joinedload : Pour les relations one-to-one ou many-to-one
   query.options(joinedload(Model.relation))
   
   # selectinload : Pour les relations one-to-many (plus efficace)
   query.options(selectinload(Model.relations))

2. Chaîner les eager loads pour les relations imbriquées :
   
   query.options(
       joinedload(Recette.ingredients).joinedload(IngredientRecette.ingredient)
   )

3. Utiliser les requêtes agrégées plutôt que Python :
   
   # MAUVAIS
   total = sum(item.prix for item in items)
   
   # BON
   total = db.session.query(func.sum(Model.prix)).scalar()

4. Paginer côté base de données :
   
   query.offset((page-1) * per_page).limit(per_page).all()

5. Indexer les colonnes fréquemment utilisées dans les WHERE/ORDER BY :
   
   # Dans models.py
   __table_args__ = (
       db.Index('idx_nom', 'nom'),
   )
"""
