from flask import Blueprint, render_template
from models.models import db, RecettePlanifiee, Recette
from sqlalchemy import func, desc
from datetime import datetime, timedelta
from collections import defaultdict

historique_bp = Blueprint('historique', __name__)

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
    
    cout_total = 0
    nb_recettes_avec_prix = 0
    for prep in historique:
        cout = prep.recette_ref.calculer_cout()
        if cout > 0:
            cout_total += cout
            nb_recettes_avec_prix += 1
    cout_moyen = cout_total / nb_recettes_avec_prix if nb_recettes_avec_prix > 0 else 0
    
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
    
    return render_template('historique.html',
                         historique=historique,
                         top_recettes=top_recettes,
                         stats={
                             'total': total_recettes,
                             'mois': recettes_mois,
                             'semaine': recettes_semaine,
                             'cout_moyen': cout_moyen
                         },
                         graphique_mois=graphique_mois,
                         graphique_top=graphique_top)
