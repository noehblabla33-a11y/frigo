from flask import Blueprint, render_template, request, redirect, url_for, flash
from models.models import db, RecettePlanifiee
from datetime import datetime
from utils.courses import retirer_ingredients_courses, deduire_ingredients_frigo

planification_bp = Blueprint('planification', __name__)

@planification_bp.route('/', methods=['GET', 'POST'])
def liste():
    """
    Redirige vers la page 'Cuisiner avec mon frigo' qui contient maintenant
    les recettes planifiées
    """
    return redirect(url_for('recettes.cuisiner_avec_frigo'))

@planification_bp.route('/preparer/<int:id>')
def preparer(id):
    """Marquer une recette planifiée comme préparée et mettre à jour le frigo"""
    plan = RecettePlanifiee.query.get_or_404(id)
    plan.preparee = True
    plan.date_preparation = datetime.utcnow()
    
    # Déduire les ingrédients du frigo (fonction factorisée)
    nb_deduits = deduire_ingredients_frigo(plan.recette_id)
    
    db.session.commit()
    flash(f'✓ Recette "{plan.recette_ref.nom}" marquée comme préparée ! Le frigo a été mis à jour.', 'success')
    return redirect(url_for('recettes.cuisiner_avec_frigo'))

@planification_bp.route('/annuler/<int:id>')
def annuler(id):
    """
    Annuler une recette planifiée et retirer les ingrédients de la liste de courses
    """
    plan = RecettePlanifiee.query.get_or_404(id)
    nom_recette = plan.recette_ref.nom
    
    # Retirer les ingrédients de la liste de courses (fonction factorisée)
    resultat = retirer_ingredients_courses(plan.recette_id)
    
    # Supprimer la planification
    db.session.delete(plan)
    db.session.commit()
    
    # Message personnalisé selon ce qui a été fait
    message = f'✓ Planification de "{nom_recette}" annulée.'
    if resultat['supprimes'] > 0 or resultat['retires'] > 0:
        details = []
        if resultat['supprimes'] > 0:
            details.append(f'{resultat["supprimes"]} ingrédient(s) retiré(s) de la liste de courses')
        if resultat['retires'] > 0:
            details.append(f'{resultat["retires"]} quantité(s) réduite(s)')
        message += ' ' + ', '.join(details) + '.'
    
    flash(message, 'info')
    return redirect(url_for('recettes.cuisiner_avec_frigo'))
