from flask import Blueprint, render_template
from models.models import db, RecettePlanifiee, Recette, IngredientRecette, Ingredient
from sqlalchemy import func, desc
from datetime import datetime, timedelta
from collections import defaultdict
import calendar

historique_bp = Blueprint('historique', __name__)

def calculer_statistiques_categories(historique):
    """Calcule les statistiques de consommation par catégorie d'ingrédients"""
    categories_count = defaultdict(int)
    categories_cout = defaultdict(float)
    
    for prep in historique:
        for ing_rec in prep.recette_ref.ingredients:
            categorie = ing_rec.ingredient.categorie or 'Non catégorisé'
            categories_count[categorie] += 1
            if ing_rec.ingredient.prix_unitaire > 0:
                categories_cout[categorie] += ing_rec.quantite * ing_rec.ingredient.prix_unitaire
    
    return {
        'labels': list(categories_count.keys()),
        'counts': list(categories_count.values()),
        'couts': [round(v, 2) for v in categories_cout.values()]
    }

def calculer_couts_periodiques(historique):
    """Calcule les coûts moyens par semaine et par mois"""
    couts_semaine = defaultdict(float)
    couts_mois = defaultdict(float)
    nb_recettes_semaine = defaultdict(int)
    nb_recettes_mois = defaultdict(int)
    
    for prep in historique:
        if prep.date_preparation:
            cout = prep.recette_ref.calculer_cout()
            if cout > 0:
                # Calcul par semaine (année + numéro de semaine)
                semaine_key = prep.date_preparation.strftime('%Y-W%W')
                couts_semaine[semaine_key] += cout
                nb_recettes_semaine[semaine_key] += 1
                
                # Calcul par mois
                mois_key = prep.date_preparation.strftime('%Y-%m')
                couts_mois[mois_key] += cout
                nb_recettes_mois[mois_key] += 1
    
    # Prendre les 8 dernières semaines et calculer les moyennes
    semaines_triees = sorted(couts_semaine.items(), key=lambda x: x[0])[-8:]
    semaines_moyennes = []
    semaines_labels_formatees = []
    
    for semaine_key, cout_total in semaines_triees:
        nb_recettes = nb_recettes_semaine[semaine_key]
        cout_moyen = cout_total / nb_recettes if nb_recettes > 0 else 0
        semaines_moyennes.append(round(cout_moyen, 2))
        # Format: "S48 2024"
        semaines_labels_formatees.append(semaine_key.replace('W', ' S'))
    
    # Prendre les 6 derniers mois et calculer les moyennes
    mois_tries = sorted(couts_mois.items(), key=lambda x: x[0])[-6:]
    mois_moyens = []
    mois_labels_formates = []
    
    for mois_key, cout_total in mois_tries:
        nb_recettes = nb_recettes_mois[mois_key]
        cout_moyen = cout_total / nb_recettes if nb_recettes > 0 else 0
        mois_moyens.append(round(cout_moyen, 2))
        # Convertir "2024-12" en "Déc 2024"
        date = datetime.strptime(mois_key, '%Y-%m')
        mois_labels_formates.append(date.strftime('%b %Y'))
    
    return {
        'semaines': {
            'labels': semaines_labels_formatees,
            'couts_moyens': semaines_moyennes,
            'couts_totaux': [s[1] for s in semaines_triees]
        },
        'mois': {
            'labels': mois_labels_formates,
            'couts_moyens': mois_moyens,
            'couts_totaux': [round(m[1], 2) for m in mois_tries]
        }
    }

def calculer_ingredients_populaires(historique, limit=10):
    """Calcule les ingrédients les plus utilisés"""
    ingredients_count = defaultdict(lambda: {'count': 0, 'quantite': 0, 'nom': '', 'unite': ''})
    
    for prep in historique:
        for ing_rec in prep.recette_ref.ingredients:
            ing_id = ing_rec.ingredient.id
            ingredients_count[ing_id]['count'] += 1
            ingredients_count[ing_id]['quantite'] += ing_rec.quantite
            ingredients_count[ing_id]['nom'] = ing_rec.ingredient.nom
            ingredients_count[ing_id]['unite'] = ing_rec.ingredient.unite
    
    # Trier par nombre d'utilisations
    ingredients_tries = sorted(
        ingredients_count.values(),
        key=lambda x: x['count'],
        reverse=True
    )[:limit]
    
    return {
        'labels': [ing['nom'] for ing in ingredients_tries],
        'counts': [ing['count'] for ing in ingredients_tries],
        'quantites': [round(ing['quantite'], 1) for ing in ingredients_tries],
        'unites': [ing['unite'] for ing in ingredients_tries]
    }

@historique_bp.route('/')
def liste():
    historique = RecettePlanifiee.query.filter_by(preparee=True)\
        .order_by(desc(RecettePlanifiee.date_preparation)).all()
    
    top_recettes = db.session.query(
        Recette.nom,
        Recette.id,
        func.count(RecettePlanifiee.id).label('nb_preparations')
    ).join(RecettePlanifiee, Recette.id == RecettePlanifiee.recette_id)\
     .filter(RecettePlanifiee.preparee == True)\
     .group_by(Recette.id)\
     .order_by(desc('nb_preparations'))\
     .limit(10).all()
    
    debut_mois = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    recettes_mois = RecettePlanifiee.query.filter(
        RecettePlanifiee.preparee == True,
        RecettePlanifiee.date_preparation >= debut_mois
    ).count()
    
    debut_semaine = datetime.utcnow() - timedelta(days=datetime.utcnow().weekday())
    debut_semaine = debut_semaine.replace(hour=0, minute=0, second=0, microsecond=0)
    recettes_semaine = RecettePlanifiee.query.filter(
        RecettePlanifiee.preparee == True,
        RecettePlanifiee.date_preparation >= debut_semaine
    ).count()
    
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
    
    # Calcul du coût moyen du mois en cours
    cout_mois_courant = 0
    for prep in historique:
        if prep.date_preparation and prep.date_preparation >= debut_mois:
            cout_mois_courant += prep.recette_ref.calculer_cout()
    cout_moyen_mois = cout_mois_courant / recettes_mois if recettes_mois > 0 else 0
    
    # Calcul du coût moyen de la semaine en cours
    cout_semaine_courante = 0
    for prep in historique:
        if prep.date_preparation and prep.date_preparation >= debut_semaine:
            cout_semaine_courante += prep.recette_ref.calculer_cout()
    cout_moyen_semaine = cout_semaine_courante / recettes_semaine if recettes_semaine > 0 else 0
    
    # Graphique des recettes par mois (existant)
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
