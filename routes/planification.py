from flask import Blueprint, render_template, request, redirect, url_for, flash
from models.models import db, Recette, RecettePlanifiee, IngredientRecette, ListeCourses, StockFrigo
from datetime import datetime

planification_bp = Blueprint('planification', __name__)

@planification_bp.route('/', methods=['GET', 'POST'])
def liste():
    if request.method == 'POST':
        recette_id = request.form.get('recette_id')
        
        planifiee = RecettePlanifiee(recette_id=recette_id)
        db.session.add(planifiee)
        
        ingredients_recette = IngredientRecette.query.filter_by(recette_id=recette_id).all()
        for ing_rec in ingredients_recette:
            stock = StockFrigo.query.filter_by(ingredient_id=ing_rec.ingredient_id).first()
            quantite_disponible = stock.quantite if stock else 0
            
            if quantite_disponible < ing_rec.quantite:
                manquant = ing_rec.quantite - quantite_disponible
                
                item = ListeCourses.query.filter_by(
                    ingredient_id=ing_rec.ingredient_id, 
                    achete=False
                ).first()
                
                if item:
                    item.quantite += manquant
                else:
                    item = ListeCourses(
                        ingredient_id=ing_rec.ingredient_id, 
                        quantite=manquant
                    )
                    db.session.add(item)
        
        db.session.commit()
        flash('Recette planifiée ! Consultez votre liste de courses.', 'success')
        return redirect(url_for('planification.liste'))
    
    recettes = Recette.query.all()
    planifiees = RecettePlanifiee.query.filter_by(preparee=False).all()
    
    return render_template('planifier.html', recettes=recettes, planifiees=planifiees)

@planification_bp.route('/preparer/<int:id>')
def preparer(id):
    plan = RecettePlanifiee.query.get_or_404(id)
    plan.preparee = True
    plan.date_preparation = datetime.utcnow()
    
    ingredients_recette = IngredientRecette.query.filter_by(recette_id=plan.recette_id).all()
    for ing_rec in ingredients_recette:
        stock = StockFrigo.query.filter_by(ingredient_id=ing_rec.ingredient_id).first()
        if stock:
            stock.quantite = max(0, stock.quantite - ing_rec.quantite)
    
    db.session.commit()
    flash('Recette marquée comme préparée ! Le frigo a été mis à jour.', 'success')
    return redirect(url_for('planification.liste'))

@planification_bp.route('/annuler/<int:id>')
def annuler(id):
    plan = RecettePlanifiee.query.get_or_404(id)
    
    # Récupérer les ingrédients de la recette planifiée
    ingredients_recette = IngredientRecette.query.filter_by(recette_id=plan.recette_id).all()
    
    # Pour chaque ingrédient, réduire ou supprimer de la liste de courses
    for ing_rec in ingredients_recette:
        stock = StockFrigo.query.filter_by(ingredient_id=ing_rec.ingredient_id).first()
        quantite_disponible = stock.quantite if stock else 0
        
        # Calculer ce qui avait été ajouté à la liste de courses
        if quantite_disponible < ing_rec.quantite:
            manquant = ing_rec.quantite - quantite_disponible
            
            # Trouver l'item dans la liste de courses
            item = ListeCourses.query.filter_by(
                ingredient_id=ing_rec.ingredient_id,
                achete=False
            ).first()
            
            if item:
                # Réduire la quantité ou supprimer si nécessaire
                if item.quantite <= manquant:
                    db.session.delete(item)
                else:
                    item.quantite -= manquant
    
    db.session.delete(plan)
    db.session.commit()
    flash('Recette annulée et liste de courses mise à jour.', 'info')
    return redirect(url_for('planification.liste'))
