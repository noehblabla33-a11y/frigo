"""
utils/dashboard.py
Service centralisé pour les données du Dashboard

Fournit toutes les statistiques et données nécessaires à l'affichage
du tableau de bord de la page d'accueil.

✅ NOUVEAU : Créé pour le Dashboard Dynamique
"""
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy import func, desc
from sqlalchemy.orm import joinedload

from models.models import (
    db, Ingredient, StockFrigo, Recette, RecettePlanifiee, 
    ListeCourses, IngredientRecette
)
from utils.saisons import get_saison_actuelle


# ============================================
# DATACLASSES POUR TYPAGE FORT
# ============================================

@dataclass
class StatsFrigo:
    """Statistiques du frigo"""
    nb_items: int
    valeur_totale: float
    categories: Dict[str, int]  # {categorie: count}


@dataclass
class StatsCourses:
    """Statistiques de la liste de courses"""
    nb_items: int
    cout_estime: float


@dataclass
class StatsRecettes:
    """Statistiques des recettes"""
    nb_total: int
    nb_realisables: int  # Avec tous les ingrédients disponibles
    nb_planifiees: int


@dataclass
class AlerteStock:
    """Alerte de stock bas"""
    ingredient: Ingredient
    quantite_actuelle: float
    seuil_alerte: float
    unite: str
    pourcentage_restant: float


@dataclass
class RecetteRecommandee:
    """Recette recommandée pour le dashboard"""
    recette: Recette
    score_disponibilite: float  # % d'ingrédients disponibles
    nb_ingredients_manquants: int
    cout_estime: float
    est_de_saison: bool
    temps_preparation: Optional[int]


@dataclass
class StatsActivite:
    """Statistiques d'activité récente"""
    recettes_semaine: int
    recettes_mois: int
    cout_semaine: float
    cout_mois: float
    derniere_recette: Optional[RecettePlanifiee]


@dataclass
class DashboardData:
    """Conteneur principal pour toutes les données du dashboard"""
    stats_frigo: StatsFrigo
    stats_courses: StatsCourses
    stats_recettes: StatsRecettes
    stats_activite: StatsActivite
    alertes_stock: List[AlerteStock]
    suggestions_recettes: List[RecetteRecommandee]
    saison_actuelle: str
    date_mise_a_jour: datetime


# ============================================
# FONCTIONS DE CALCUL
# ============================================

def calculer_stats_frigo() -> StatsFrigo:
    """
    Calcule les statistiques du frigo.
    
    Returns:
        StatsFrigo avec nb_items, valeur_totale, categories
    """
    stocks = StockFrigo.query.options(
        joinedload(StockFrigo.ingredient)
    ).all()
    
    nb_items = len(stocks)
    valeur_totale = 0.0
    categories = {}
    
    for stock in stocks:
        ing = stock.ingredient
        
        # Calcul de la valeur
        if ing.prix_unitaire and ing.prix_unitaire > 0:
            if ing.unite == 'pièce' and ing.poids_piece and ing.poids_piece > 0:
                valeur_totale += stock.quantite * ing.poids_piece * ing.prix_unitaire
            else:
                valeur_totale += stock.quantite * ing.prix_unitaire
        
        # Comptage par catégorie
        cat = ing.categorie or 'Autres'
        categories[cat] = categories.get(cat, 0) + 1
    
    return StatsFrigo(
        nb_items=nb_items,
        valeur_totale=round(valeur_totale, 2),
        categories=categories
    )


def calculer_stats_courses() -> StatsCourses:
    """
    Calcule les statistiques de la liste de courses.
    
    Returns:
        StatsCourses avec nb_items et cout_estime
    """
    items = ListeCourses.query.options(
        joinedload(ListeCourses.ingredient)
    ).filter_by(achete=False).all()
    
    nb_items = len(items)
    cout_estime = 0.0
    
    for item in items:
        ing = item.ingredient
        if ing and ing.prix_unitaire and ing.prix_unitaire > 0:
            if ing.unite == 'pièce' and ing.poids_piece and ing.poids_piece > 0:
                cout_estime += item.quantite * ing.poids_piece * ing.prix_unitaire
            else:
                cout_estime += item.quantite * ing.prix_unitaire
    
    return StatsCourses(
        nb_items=nb_items,
        cout_estime=round(cout_estime, 2)
    )


def calculer_stats_recettes() -> StatsRecettes:
    """
    Calcule les statistiques des recettes.
    
    Returns:
        StatsRecettes avec nb_total, nb_realisables, nb_planifiees
    """
    # Nombre total de recettes
    nb_total = Recette.query.count()
    
    # Nombre de recettes planifiées (non préparées)
    nb_planifiees = RecettePlanifiee.query.filter_by(preparee=False).count()
    
    # Nombre de recettes réalisables avec le stock actuel
    # On charge les recettes avec leurs ingrédients
    recettes = Recette.query.options(
        joinedload(Recette.ingredients).joinedload(IngredientRecette.ingredient)
    ).all()
    
    nb_realisables = 0
    for recette in recettes:
        if recette.ingredients:
            disponibilite = recette.calculer_disponibilite_ingredients()
            if disponibilite['realisable']:
                nb_realisables += 1
    
    return StatsRecettes(
        nb_total=nb_total,
        nb_realisables=nb_realisables,
        nb_planifiees=nb_planifiees
    )


def calculer_stats_activite() -> StatsActivite:
    """
    Calcule les statistiques d'activité récente.
    
    Returns:
        StatsActivite avec stats semaine/mois et dernière recette
    """
    maintenant = datetime.utcnow()
    debut_semaine = maintenant - timedelta(days=maintenant.weekday())
    debut_semaine = debut_semaine.replace(hour=0, minute=0, second=0, microsecond=0)
    debut_mois = maintenant.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # Recettes préparées cette semaine
    recettes_semaine_query = RecettePlanifiee.query.filter(
        RecettePlanifiee.preparee == True,
        RecettePlanifiee.date_preparation >= debut_semaine
    ).options(
        joinedload(RecettePlanifiee.recette_ref).joinedload(Recette.ingredients)
    ).all()
    
    recettes_semaine = len(recettes_semaine_query)
    cout_semaine = sum(
        r.recette_ref.calculer_cout() for r in recettes_semaine_query
    )
    
    # Recettes préparées ce mois
    recettes_mois_query = RecettePlanifiee.query.filter(
        RecettePlanifiee.preparee == True,
        RecettePlanifiee.date_preparation >= debut_mois
    ).options(
        joinedload(RecettePlanifiee.recette_ref).joinedload(Recette.ingredients)
    ).all()
    
    recettes_mois = len(recettes_mois_query)
    cout_mois = sum(
        r.recette_ref.calculer_cout() for r in recettes_mois_query
    )
    
    # Dernière recette préparée
    derniere = RecettePlanifiee.query.filter_by(preparee=True).options(
        joinedload(RecettePlanifiee.recette_ref)
    ).order_by(desc(RecettePlanifiee.date_preparation)).first()
    
    return StatsActivite(
        recettes_semaine=recettes_semaine,
        recettes_mois=recettes_mois,
        cout_semaine=round(cout_semaine, 2),
        cout_mois=round(cout_mois, 2),
        derniere_recette=derniere
    )


def detecter_alertes_stock(seuils_defaut: Dict[str, float] = None) -> List[AlerteStock]:
    """
    Détecte les ingrédients avec un stock bas.
    
    Args:
        seuils_defaut: Dict des seuils par défaut par unité
                      Ex: {'g': 100, 'ml': 200, 'pièce': 2}
    
    Returns:
        Liste d'AlerteStock triée par urgence
    """
    if seuils_defaut is None:
        seuils_defaut = {
            'g': 100,      # Alerter si < 100g
            'ml': 250,     # Alerter si < 250ml
            'pièce': 2     # Alerter si < 2 pièces
        }
    
    stocks = StockFrigo.query.options(
        joinedload(StockFrigo.ingredient)
    ).all()
    
    alertes = []
    
    for stock in stocks:
        ing = stock.ingredient
        seuil = seuils_defaut.get(ing.unite, 100)
        
        if stock.quantite < seuil and stock.quantite > 0:
            pourcentage = (stock.quantite / seuil) * 100 if seuil > 0 else 0
            
            alertes.append(AlerteStock(
                ingredient=ing,
                quantite_actuelle=stock.quantite,
                seuil_alerte=seuil,
                unite=ing.unite,
                pourcentage_restant=round(pourcentage, 1)
            ))
    
    # Trier par pourcentage restant (plus bas = plus urgent)
    alertes.sort(key=lambda a: a.pourcentage_restant)
    
    return alertes[:5]  # Retourner les 5 plus urgentes


def get_suggestions_recettes(limite: int = 3) -> List[RecetteRecommandee]:
    """
    Suggère des recettes basées sur le stock actuel et la saison.
    
    Args:
        limite: Nombre max de suggestions
    
    Returns:
        Liste de RecetteRecommandee triée par pertinence
    """
    saison_actuelle = get_saison_actuelle()
    
    # Charger toutes les recettes avec leurs ingrédients
    recettes = Recette.query.options(
        joinedload(Recette.ingredients).joinedload(IngredientRecette.ingredient)
    ).all()
    
    # Récupérer l'historique récent pour éviter les répétitions
    historique_recent = set()
    recettes_recentes = RecettePlanifiee.query.filter(
        RecettePlanifiee.preparee == True,
        RecettePlanifiee.date_preparation >= datetime.utcnow() - timedelta(days=14)
    ).all()
    for rp in recettes_recentes:
        historique_recent.add(rp.recette_id)
    
    suggestions = []
    
    for recette in recettes:
        if not recette.ingredients:
            continue
        
        # Calculer la disponibilité
        disponibilite = recette.calculer_disponibilite_ingredients()
        score_dispo = disponibilite['pourcentage']
        nb_manquants = len(disponibilite['ingredients_manquants'])
        
        # Calculer le score saisonnier
        score_saison = recette.calculer_score_saisonnier(saison_actuelle)
        est_de_saison = score_saison['score'] >= 70
        
        # Calculer le coût
        cout = recette.calculer_cout()
        
        # Pénaliser les recettes récemment préparées
        if recette.id in historique_recent:
            score_dispo *= 0.5  # Réduire le score de moitié
        
        suggestions.append(RecetteRecommandee(
            recette=recette,
            score_disponibilite=score_dispo,
            nb_ingredients_manquants=nb_manquants,
            cout_estime=cout,
            est_de_saison=est_de_saison,
            temps_preparation=recette.temps_preparation
        ))
    
    # Trier par score de disponibilité décroissant, puis par saison
    suggestions.sort(
        key=lambda s: (s.score_disponibilite, s.est_de_saison, -s.nb_ingredients_manquants),
        reverse=True
    )
    
    return suggestions[:limite]


def get_recettes_planifiees_a_venir() -> List[RecettePlanifiee]:
    """
    Récupère les recettes planifiées non encore préparées.
    
    Returns:
        Liste des recettes planifiées
    """
    return RecettePlanifiee.query.filter_by(preparee=False).options(
        joinedload(RecettePlanifiee.recette_ref)
    ).order_by(RecettePlanifiee.date_planification).limit(5).all()


# ============================================
# FONCTION PRINCIPALE
# ============================================

def get_dashboard_data() -> DashboardData:
    """
    Récupère toutes les données nécessaires au dashboard.
    
    Cette fonction centralise tous les appels pour optimiser
    les performances et éviter les requêtes multiples.
    
    Returns:
        DashboardData contenant toutes les statistiques
    """
    return DashboardData(
        stats_frigo=calculer_stats_frigo(),
        stats_courses=calculer_stats_courses(),
        stats_recettes=calculer_stats_recettes(),
        stats_activite=calculer_stats_activite(),
        alertes_stock=detecter_alertes_stock(),
        suggestions_recettes=get_suggestions_recettes(limite=3),
        saison_actuelle=get_saison_actuelle(),
        date_mise_a_jour=datetime.utcnow()
    )


# ============================================
# FONCTIONS UTILITAIRES POUR LE TEMPLATE
# ============================================

def formater_valeur_euros(valeur: float) -> str:
    """Formate une valeur en euros."""
    if valeur >= 1000:
        return f"{valeur/1000:.1f}k€"
    return f"{valeur:.2f}€"


def get_emoji_categorie(categorie: str) -> str:
    """Retourne un emoji pour une catégorie d'ingrédient."""
    emojis = {
        'Fruits': '🍎',
        'Légumes': '🥕',
        'Viandes': '🥩',
        'Poissons': '🐟',
        'Produits laitiers': '🧀',
        'Épices': '🌶️',
        'Céréales': '🌾',
        'Boissons': '🥤',
        'Surgelés': '🧊',
        'Conserves': '🥫',
        'Autres': '📦'
    }
    return emojis.get(categorie, '📦')


def get_couleur_alerte(pourcentage: float) -> str:
    """Retourne une couleur CSS selon le niveau d'alerte."""
    if pourcentage < 25:
        return '#dc3545'  # Rouge - critique
    elif pourcentage < 50:
        return '#fd7e14'  # Orange - attention
    else:
        return '#ffc107'  # Jaune - info
