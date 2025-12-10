# ============================================
# Fichier: routes/historique.py (CORRIGÉ)
# Corrections des requêtes SQL pour les graphiques
# ============================================

from flask import Blueprint, render_template, jsonify
from sqlalchemy import func, desc, case
from sqlalchemy.orm import joinedload
from datetime import datetime, timedelta
from collections import defaultdict

from models import db, RecettePlanifiee, Recette, Ingredient, IngredientRecette

historique_bp = Blueprint('historique', __name__, url_prefix='/historique')


def calculer_statistiques_categories():
    """
    Calculer les statistiques par catégorie d'ingrédients
    """
    
    stats = db.session.query(
        func.coalesce(Ingredient.categorie, 'Autres').label('categorie'),
        func.count(IngredientRecette.id).label('count'),
        func.sum(IngredientRecette.quantite * Ingredient.prix_unitaire).label('cout')
    ).select_from(RecettePlanifiee)\
    .join(Recette, RecettePlanifiee.recette_id == Recette.id)\
    .join(IngredientRecette, Recette.id == IngredientRecette.recette_id)\
    .join(Ingredient, IngredientRecette.ingredient_id == Ingredient.id)\
    .filter(RecettePlanifiee.preparee == True)\
    .group_by('categorie')\
    .all()
    
    return {
        'labels': [s.categorie for s in stats],
        'counts': [s.count for s in stats],
        'couts': [round(s.cout or 0, 2) for s in stats]
    }


def calculer_couts_periodiques():
    """
    Calculer les coûts moyens par semaine et par mois
    CORRIGÉ : Meilleure gestion des dates et périodes
    """
    
    # Date de référence
    aujourd_hui = datetime.utcnow()
    debut_periode = aujourd_hui - timedelta(days=90)  # 3 derniers mois
    
    # ========================================
    # STATISTIQUES PAR SEMAINE (8 dernières)
    # ========================================
    stats_semaines = db.session.query(
        func.strftime('%Y-%W', RecettePlanifiee.date_preparation).label('semaine'),
        func.count(RecettePlanifiee.id).label('count'),
        func.sum(IngredientRecette.quantite * Ingredient.prix_unitaire).label('cout_total')
    ).select_from(RecettePlanifiee)\
    .join(Recette, RecettePlanifiee.recette_id == Recette.id)\
    .join(IngredientRecette, Recette.id == IngredientRecette.recette_id)\
    .join(Ingredient, IngredientRecette.ingredient_id == Ingredient.id)\
    .filter(
        RecettePlanifiee.preparee == True,
        RecettePlanifiee.date_preparation >= debut_periode
    ).group_by('semaine')\
    .order_by('semaine')\
    .all()
    
    # Créer un dictionnaire pour accès facile
    semaines_dict = {s.semaine: {'count': s.count, 'cout_total': s.cout_total or 0} for s in stats_semaines}
    
    # Formater pour les 8 dernières semaines
    semaines_labels = []
    semaines_couts_moyens = []
    semaines_couts_totaux = []
    
    for i in range(7, -1, -1):  # 8 dernières semaines
        date = aujourd_hui - timedelta(weeks=i)
        semaine_key = date.strftime('%Y-%W')
        semaine_label = f"S{date.strftime('%W')}"
        
        semaines_labels.append(semaine_label)
        
        if semaine_key in semaines_dict:
            count = semaines_dict[semaine_key]['count']
            cout_total = semaines_dict[semaine_key]['cout_total']
            cout_moyen = cout_total / count if count > 0 else 0
        else:
            cout_total = 0
            cout_moyen = 0
        
        semaines_couts_moyens.append(round(cout_moyen, 2))
        semaines_couts_totaux.append(round(cout_total, 2))
    
    # ========================================
    # STATISTIQUES PAR MOIS (6 derniers)
    # ========================================
    debut_periode_mois = aujourd_hui - timedelta(days=180)  # 6 derniers mois
    
    stats_mois = db.session.query(
        func.strftime('%Y-%m', RecettePlanifiee.date_preparation).label('mois'),
        func.count(RecettePlanifiee.id).label('count'),
        func.sum(IngredientRecette.quantite * Ingredient.prix_unitaire).label('cout_total')
    ).select_from(RecettePlanifiee)\
    .join(Recette, RecettePlanifiee.recette_id == Recette.id)\
    .join(IngredientRecette, Recette.id == IngredientRecette.recette_id)\
    .join(Ingredient, IngredientRecette.ingredient_id == Ingredient.id)\
    .filter(
        RecettePlanifiee.preparee == True,
        RecettePlanifiee.date_preparation >= debut_periode_mois
    ).group_by('mois')\
    .order_by('mois')\
    .all()
    
    # Créer un dictionnaire
    mois_dict = {s.mois: {'count': s.count, 'cout_total': s.cout_total or 0} for s in stats_mois}
    
    # Formater pour les 6 derniers mois
    mois_labels = []
    mois_couts_moyens = []
    mois_couts_totaux = []
    
    for i in range(5, -1, -1):  # 6 derniers mois
        date = (aujourd_hui.replace(day=1) - timedelta(days=30*i))
        mois_key = date.strftime('%Y-%m')
        mois_label = date.strftime('%b %Y')
        
        mois_labels.append(mois_label)
        
        if mois_key in mois_dict:
            count = mois_dict[mois_key]['count']
            cout_total = mois_dict[mois_key]['cout_total']
            cout_moyen = cout_total / count if count > 0 else 0
        else:
            cout_total = 0
            cout_moyen = 0
        
        mois_couts_moyens.append(round(cout_moyen, 2))
        mois_couts_totaux.append(round(cout_total, 2))
    
    return {
        'semaines': {
            'labels': semaines_labels,
            'couts_moyens': semaines_couts_moyens,
            'couts_totaux': semaines_couts_totaux
        },
        'mois': {
            'labels': mois_labels,
            'couts_moyens': mois_couts_moyens,
            'couts_totaux': mois_couts_totaux
        }
    }


def calculer_ingredients_populaires(limit=10):
    """
    Calculer les ingrédients les plus utilisés
    CORRIGÉ : Ordre de JOIN explicite
    """
    
    top_ingredients = db.session.query(
        Ingredient.nom,
        Ingredient.unite,
        func.count(IngredientRecette.id).label('count'),
        func.sum(IngredientRecette.quantite).label('quantite_totale')
    ).select_from(RecettePlanifiee)\
    .join(Recette, RecettePlanifiee.recette_id == Recette.id)\
    .join(IngredientRecette, Recette.id == IngredientRecette.recette_id)\
    .join(Ingredient, IngredientRecette.ingredient_id == Ingredient.id)\
    .filter(RecettePlanifiee.preparee == True)\
    .group_by(Ingredient.id, Ingredient.nom, Ingredient.unite)\
    .order_by(desc('count'))\
    .limit(limit)\
    .all()
    
    return {
        'labels': [ing.nom for ing in top_ingredients],
        'counts': [ing.count for ing in top_ingredients],
        'quantites': [round(ing.quantite_totale, 1) for ing in top_ingredients],
        'unites': [ing.unite for ing in top_ingredients]
    }


@historique_bp.route('/')
def liste():
    """
    Page principale de l'historique avec statistiques
    OPTIMISÉ : Moins de requêtes, meilleur caching
    """
    
    # Dates de référence
    debut_mois = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    debut_semaine = datetime.utcnow() - timedelta(days=datetime.utcnow().weekday())
    debut_semaine = debut_semaine.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # ========================================
    # 1. HISTORIQUE avec eager loading
    # ========================================
    historique = RecettePlanifiee.query\
        .filter_by(preparee=True)\
        .options(joinedload(RecettePlanifiee.recette_ref))\
        .order_by(desc(RecettePlanifiee.date_preparation))\
        .limit(50)\
        .all()
    
    # ========================================
    # 2. TOP 10 des recettes
    # ========================================
    top_recettes = db.session.query(
        Recette.nom,
        Recette.id,
        func.count(RecettePlanifiee.id).label('nb_preparations')
    ).join(RecettePlanifiee, Recette.id == RecettePlanifiee.recette_id)\
    .filter(RecettePlanifiee.preparee == True)\
    .group_by(Recette.id, Recette.nom)\
    .order_by(desc('nb_preparations'))\
    .limit(10)\
    .all()
    
    # ========================================
    # 3. COMPTEURS COMBINÉS (1 requête)
    # ========================================
    stats_counts = db.session.query(
        func.count(RecettePlanifiee.id).label('total'),
        func.sum(case(
            (RecettePlanifiee.date_preparation >= debut_mois, 1),
            else_=0
        )).label('mois'),
        func.sum(case(
            (RecettePlanifiee.date_preparation >= debut_semaine, 1),
            else_=0
        )).label('semaine')
    ).filter(RecettePlanifiee.preparee == True).first()
    
    total_recettes = stats_counts.total or 0
    recettes_mois = stats_counts.mois or 0
    recettes_semaine = stats_counts.semaine or 0
    
    # ========================================
    # 4. COÛTS COMBINÉS (1 requête)
    # ========================================
    stats_couts = db.session.query(
        func.sum(IngredientRecette.quantite * Ingredient.prix_unitaire).label('cout_total'),
        func.sum(case(
            (RecettePlanifiee.date_preparation >= debut_mois,
             IngredientRecette.quantite * Ingredient.prix_unitaire),
            else_=0
        )).label('cout_mois'),
        func.sum(case(
            (RecettePlanifiee.date_preparation >= debut_semaine,
             IngredientRecette.quantite * Ingredient.prix_unitaire),
            else_=0
        )).label('cout_semaine')
    ).select_from(RecettePlanifiee)\
    .join(Recette, RecettePlanifiee.recette_id == Recette.id)\
    .join(IngredientRecette, Recette.id == IngredientRecette.recette_id)\
    .join(Ingredient, IngredientRecette.ingredient_id == Ingredient.id)\
    .filter(RecettePlanifiee.preparee == True)\
    .first()
    
    cout_total = stats_couts.cout_total or 0
    cout_mois_courant = stats_couts.cout_mois or 0
    cout_semaine_courante = stats_couts.cout_semaine or 0
    
    # Calculer les moyennes
    cout_moyen = cout_total / total_recettes if total_recettes > 0 else 0
    cout_moyen_mois = cout_mois_courant / recettes_mois if recettes_mois > 0 else 0
    cout_moyen_semaine = cout_semaine_courante / recettes_semaine if recettes_semaine > 0 else 0
    
    # ========================================
    # 5. GRAPHIQUE DES RECETTES PAR MOIS
    # ========================================
    mois_data = defaultdict(int)
    for prep in historique:
        if prep.date_preparation:
            mois_annee = prep.date_preparation.strftime('%Y-%m')
            mois_data[mois_annee] += 1
    
    mois_labels = []
    mois_values = []
    for i in range(5, -1, -1):
        date = datetime.utcnow() - timedelta(days=30*i)
        mois_key = date.strftime('%Y-%m')
        mois_label = date.strftime('%b %Y')
        mois_labels.append(mois_label)
        mois_values.append(mois_data.get(mois_key, 0))
    
    graphique_mois = {
        'labels': mois_labels,
        'data': mois_values
    }
    
    graphique_top = {
        'labels': [r.nom for r in top_recettes],
        'data': [r.nb_preparations for r in top_recettes]
    }
    
    # ========================================
    # 6. STATISTIQUES AVANCÉES (graphiques)
    # ========================================
    stats_categories = calculer_statistiques_categories()
    couts_periodiques = calculer_couts_periodiques()
    ingredients_populaires = calculer_ingredients_populaires(limit=10)
    
    # ========================================
    # RENDU DU TEMPLATE
    # ========================================
    return render_template('historique.html',
                         historique=historique,
                         top_recettes=top_recettes,
                         stats={
                             'total': total_recettes,
                             'mois': recettes_mois,
                             'semaine': recettes_semaine,
                             'cout_moyen': cout_moyen,
                             'cout_moyen_mois': cout_moyen_mois,
                             'cout_moyen_semaine': cout_moyen_semaine,
                             'cout_total_mois': cout_mois_courant,
                             'cout_total_semaine': cout_semaine_courante
                         },
                         graphique_mois=graphique_mois,
                         graphique_top=graphique_top,
                         stats_categories=stats_categories,
                         couts_periodiques=couts_periodiques,
                         ingredients_populaires=ingredients_populaires)


# ========================================
# ROUTES API (pour debugging ou AJAX)
# ========================================

@historique_bp.route('/api/couts-par-mois')
def couts_par_mois():
    """
    API pour les coûts par mois (pour debugging)
    """
    
    aujourd_hui = datetime.utcnow()
    debut_periode = aujourd_hui - timedelta(days=365)
    
    stats_mois = db.session.query(
        func.strftime('%Y-%m', RecettePlanifiee.date_preparation).label('mois'),
        func.count(RecettePlanifiee.id).label('count'),
        func.sum(IngredientRecette.quantite * Ingredient.prix_unitaire).label('cout_total')
    ).select_from(RecettePlanifiee)\
    .join(Recette, RecettePlanifiee.recette_id == Recette.id)\
    .join(IngredientRecette, Recette.id == IngredientRecette.recette_id)\
    .join(Ingredient, IngredientRecette.ingredient_id == Ingredient.id)\
    .filter(
        RecettePlanifiee.preparee == True,
        RecettePlanifiee.date_preparation >= debut_periode
    ).group_by('mois').all()
    
    stats_dict = {s.mois: {'count': s.count, 'cout_total': s.cout_total or 0} for s in stats_mois}
    
    mois_labels = []
    counts = []
    couts_moyens = []
    
    for i in range(12):
        date = aujourd_hui.replace(day=1) - timedelta(days=30 * i)
        mois_key = date.strftime('%Y-%m')
        mois_labels.insert(0, date.strftime('%b %Y'))
        
        if mois_key in stats_dict:
            count = stats_dict[mois_key]['count']
            cout_total = stats_dict[mois_key]['cout_total']
            cout_moyen = cout_total / count if count > 0 else 0
        else:
            count = 0
            cout_moyen = 0
        
        counts.insert(0, count)
        couts_moyens.insert(0, round(cout_moyen, 2))
    
    return jsonify({
        'labels': mois_labels,
        'counts': counts,
        'couts_moyens': couts_moyens
    })


@historique_bp.route('/api/ingredients-utilises')
def ingredients_utilises():
    """
    API pour les ingrédients les plus utilisés (pour debugging)
    """
    
    top_ingredients = db.session.query(
        Ingredient.nom,
        Ingredient.unite,
        func.count(IngredientRecette.id).label('count'),
        func.sum(IngredientRecette.quantite).label('quantite_totale')
    ).select_from(RecettePlanifiee)\
    .join(Recette, RecettePlanifiee.recette_id == Recette.id)\
    .join(IngredientRecette, Recette.id == IngredientRecette.recette_id)\
    .join(Ingredient, IngredientRecette.ingredient_id == Ingredient.id)\
    .filter(RecettePlanifiee.preparee == True)\
    .group_by(Ingredient.id, Ingredient.nom, Ingredient.unite)\
    .order_by(desc('count'))\
    .limit(10)\
    .all()
    
    return jsonify({
        'labels': [ing.nom for ing in top_ingredients],
        'counts': [ing.count for ing in top_ingredients],
        'quantites': [round(ing.quantite_totale, 1) for ing in top_ingredients],
        'unites': [ing.unite for ing in top_ingredients]
    })
