"""
routes/historique.py - VERSION OPTIMISÉE AVEC CONTEXT MANAGERS
Gestion de l'historique des recettes préparées

NOTE: Ce fichier n'a PAS besoin de modifications majeures car il ne contient
que des opérations de LECTURE (pas de db.session.commit).

Les seuls commits sont dans routes/planification.py (fonction preparer)
qui est déjà optimisée ci-dessous.
"""
from flask import Blueprint, render_template, jsonify
from models.models import db, Recette, RecettePlanifiee, Ingredient
from sqlalchemy import func, desc
from datetime import datetime, timedelta

historique_bp = Blueprint('historique', __name__)


@historique_bp.route('/api/stats-mensuelles')
def stats_mensuelles():
    """API pour les statistiques mensuelles (pour graphiques)"""
    from collections import defaultdict
    
    # Récupérer les 12 derniers mois
    aujourd_hui = datetime.utcnow()
    stats_par_mois = defaultdict(lambda: {'count': 0, 'couts': []})
    
    # Récupérer' toutes les recettes préparées des 12 derniers mois
    debut_periode = aujourd_hui.replace(day=1) - timedelta(days=365)
    historique = RecettePlanifiee.query.filter(
        RecettePlanifiee.preparee == True,
        RecettePlanifiee.date_preparation >= debut_periode
    ).all()
    
    for prep in historique:
        if prep.date_preparation:
            mois_annee = prep.date_preparation.strftime('%Y-%m')
            stats_par_mois[mois_annee]['count'] += 1
            cout = prep.recette_ref.calculer_cout()
            if cout > 0:
                stats_par_mois[mois_annee]['couts'].append(cout)
    
    # Formater pour le graphique
    mois_labels = []
    counts = []
    couts_moyens = []
    
    for i in range(12):
        date = aujourd_hui.replace(day=1) - timedelta(days=30 * i)
        mois_annee = date.strftime('%Y-%m')
        mois_labels.insert(0, date.strftime('%b %Y'))
        
        count = stats_par_mois[mois_annee]['count']
        counts.insert(0, count)
        
        couts = stats_par_mois[mois_annee]['couts']
        cout_moyen = sum(couts) / len(couts) if couts else 0
        couts_moyens.insert(0, round(cout_moyen, 2))
    
    return jsonify({
        'labels': mois_labels,
        'counts': counts,
        'couts_moyens': couts_moyens
    })


@historique_bp.route('/api/ingredients-utilises')
def ingredients_utilises():
    """API pour les ingrédients les plus utilisés"""
    from collections import Counter
    
    # Récupérer toutes les recettes préparées
    recettes_preparees = RecettePlanifiee.query.filter_by(preparee=True).all()
    
    # Compter les ingrédients
    ingredient_counts = Counter()
    
    for prep in recettes_preparees:
        for ing_recette in prep.recette_ref.ingredients_recette:
            ingredient_counts[ing_recette.ingredient.nom] += 1
    
    # Top 10
    ingredients_tries = [
        {'nom': nom, 'count': count, 'unite': Ingredient.query.filter_by(nom=nom).first().unite}
        for nom, count in ingredient_counts.most_common(10)
    ]
    
    return jsonify({
        'labels': [ing['nom'] for ing in ingredients_tries],
        'counts': [ing['count'] for ing in ingredients_tries],
        'unites': [ing['unite'] for ing in ingredients_tries]
    })


def calculer_statistiques_categories(historique):
    """Calculer les statistiques par catégorie d'ingrédients"""
    from collections import defaultdict
    
    categories_stats = defaultdict(lambda: {'count': 0, 'cout': 0})
    
    for prep in historique:
        for ing_rec in prep.recette_ref.ingredients_recette:
            categorie = ing_rec.ingredient.categorie or 'Autres'
            categories_stats[categorie]['count'] += 1
            
            # Calculer le coût pour cet ingrédient
            cout_ingredient = ing_rec.quantite * ing_rec.ingredient.prix_unitaire
            categories_stats[categorie]['cout'] += cout_ingredient
    
    labels = list(categories_stats.keys())
    counts = [categories_stats[cat]['count'] for cat in labels]
    couts = [round(categories_stats[cat]['cout'], 2) for cat in labels]
    
    return {
        'labels': labels,
        'counts': counts,
        'couts': couts
    }


def calculer_couts_periodiques(historique):
    """Calculer les coûts moyens par semaine et par mois"""
    from collections import defaultdict
    
    semaines_data = defaultdict(lambda: {'couts': [], 'count': 0})
    mois_data = defaultdict(lambda: {'couts': [], 'count': 0})
    
    for prep in historique:
        if prep.date_preparation:
            # Semaine
            semaine_key = prep.date_preparation.strftime('%Y-W%U')
            semaine_label = prep.date_preparation.strftime('Sem. %U')
            
            # Mois
            mois_key = prep.date_preparation.strftime('%Y-%m')
            mois_label = prep.date_preparation.strftime('%b %Y')
            
            cout = prep.recette_ref.calculer_cout()
            if cout > 0:
                semaines_data[semaine_key]['couts'].append(cout)
                semaines_data[semaine_key]['label'] = semaine_label
                
                mois_data[mois_key]['couts'].append(cout)
                mois_data[mois_key]['label'] = mois_label
    
    # Formater pour les graphiques (dernières 8 semaines)
    semaines_labels = []
    semaines_couts_moyens = []
    semaines_couts_totaux = []
    
    semaines_sorted = sorted(semaines_data.items(), key=lambda x: x[0])[-8:]
    for key, data in semaines_sorted:
        semaines_labels.append(data['label'])
        cout_moyen = sum(data['couts']) / len(data['couts']) if data['couts'] else 0
        semaines_couts_moyens.append(round(cout_moyen, 2))
        semaines_couts_totaux.append(round(sum(data['couts']), 2))
    
    # Formater pour les graphiques (derniers 6 mois)
    mois_labels = []
    mois_couts_moyens = []
    mois_couts_totaux = []
    
    mois_sorted = sorted(mois_data.items(), key=lambda x: x[0])[-6:]
    for key, data in mois_sorted:
        mois_labels.append(data['label'])
        cout_moyen = sum(data['couts']) / len(data['couts']) if data['couts'] else 0
        mois_couts_moyens.append(round(cout_moyen, 2))
        mois_couts_totaux.append(round(sum(data['couts']), 2))
    
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


def calculer_ingredients_populaires(historique, limit=10):
    """Calculer les ingrédients les plus utilisés"""
    from collections import defaultdict
    
    ingredients_stats = defaultdict(lambda: {'count': 0, 'quantite': 0, 'unite': ''})
    
    for prep in historique:
        for ing_rec in prep.recette_ref.ingredients_recette:
            nom = ing_rec.ingredient.nom
            ingredients_stats[nom]['count'] += 1
            ingredients_stats[nom]['quantite'] += ing_rec.quantite
            ingredients_stats[nom]['unite'] = ing_rec.ingredient.unite
    
    # Trier par nombre d'utilisations
    sorted_ingredients = sorted(
        ingredients_stats.items(),
        key=lambda x: x[1]['count'],
        reverse=True
    )[:limit]
    
    labels = [ing[0] for ing in sorted_ingredients]
    counts = [ing[1]['count'] for ing in sorted_ingredients]
    quantites = [round(ing[1]['quantite'], 1) for ing in sorted_ingredients]
    unites = [ing[1]['unite'] for ing in sorted_ingredients]
    
    return {
        'labels': labels,
        'counts': counts,
        'quantites': quantites,
        'unites': unites
    }


@historique_bp.route('/')
def liste():
    """Page principale de l'historique avec statistiques"""
    from collections import defaultdict
    
    # Récupérer l'historique des recettes préparées
    historique = RecettePlanifiee.query.filter_by(preparee=True)\
        .order_by(desc(RecettePlanifiee.date_preparation)).all()
    
    # Top 10 des recettes les plus préparées
    top_recettes = db.session.query(
        Recette.nom,
        Recette.id,
        func.count(RecettePlanifiee.id).label('nb_preparations')
    ).join(RecettePlanifiee, Recette.id == RecettePlanifiee.recette_id)\
     .filter(RecettePlanifiee.preparee == True)\
     .group_by(Recette.id)\
     .order_by(desc('nb_preparations'))\
     .limit(10).all()
    
    # Statistiques du mois en cours
    debut_mois = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    recettes_mois = RecettePlanifiee.query.filter(
        RecettePlanifiee.preparee == True,
        RecettePlanifiee.date_preparation >= debut_mois
    ).count()
    
    # Statistiques de la semaine en cours
    debut_semaine = datetime.utcnow() - timedelta(days=datetime.utcnow().weekday())
    debut_semaine = debut_semaine.replace(hour=0, minute=0, second=0, microsecond=0)
    recettes_semaine = RecettePlanifiee.query.filter(
        RecettePlanifiee.preparee == True,
        RecettePlanifiee.date_preparation >= debut_semaine
    ).count()
    
    # Statistiques globales
    total_recettes = RecettePlanifiee.query.filter_by(preparee=True).count()
    
    # Calculs des coûts globaux
    cout_total = 0
    nb_recettes_avec_prix = 0
    for prep in historique:
        cout = prep.recette_ref.calculer_cout()
        if cout > 0:
            cout_total += cout
            nb_recettes_avec_prix += 1
    
    cout_moyen = cout_total / nb_recettes_avec_prix if nb_recettes_avec_prix > 0 else 0
    
    # Coût moyen du mois en cours
    cout_mois_courant = 0
    for prep in historique:
        if prep.date_preparation and prep.date_preparation >= debut_mois:
            cout_mois_courant += prep.recette_ref.calculer_cout()
    
    cout_moyen_mois = cout_mois_courant / recettes_mois if recettes_mois > 0 else 0
    
    # Coût moyen de la semaine en cours
    cout_semaine_courante = 0
    for prep in historique:
        if prep.date_preparation and prep.date_preparation >= debut_semaine:
            cout_semaine_courante += prep.recette_ref.calculer_cout()
    
    cout_moyen_semaine = cout_semaine_courante / recettes_semaine if recettes_semaine > 0 else 0
    
    # Graphique des recettes par mois
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
    
    # Calculer les statistiques supplémentaires
    stats_categories = calculer_statistiques_categories(historique)
    couts_periodiques = calculer_couts_periodiques(historique)
    ingredients_populaires = calculer_ingredients_populaires(historique, limit=10)
    
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
