from flask import Blueprint, render_template, request, redirect, url_for, flash
from models.models import db, Recette, RecettePlanifiee, IngredientRecette, ListeCourses, StockFrigo
from datetime import datetime

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
    
    # Déduire les ingrédients du frigo
    ingredients_recette = IngredientRecette.query.filter_by(recette_id=plan.recette_id).all()
    for ing_rec in ingredients_recette:
        stock = StockFrigo.query.filter_by(ingredient_id=ing_rec.ingredient_id).first()
        if stock:
            stock.quantite = max(0, stock.quantite - ing_rec.quantite)
    
    db.session.commit()
    flash(f'✓ Recette "{plan.recette_ref.nom}" marquée comme préparée ! Le frigo a été mis à jour.', 'success')
    return redirect(url_for('recettes.cuisiner_avec_frigo'))

@planification_bp.route('/annuler/<int:id>')
def annuler(id):
    """Annuler une recette planifiée"""
    plan = RecettePlanifiee.query.get_or_404(id)
    nom_recette = plan.recette_ref.nom
    
    db.session.delete(plan)
    db.session.commit()
    
    flash(f'✓ Planification de "{nom_recette}" annulée.', 'info')
    return redirect(url_for('recettes.cuisiner_avec_frigo'))
