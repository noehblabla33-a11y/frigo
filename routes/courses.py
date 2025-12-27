"""
routes/courses.py (VERSION REFACTORISÉE)
Gestion de la liste de courses

CHANGEMENTS:
- Utilise utils/stock.py pour les opérations sur le stock
- Utilise utils/queries.py pour les requêtes optimisées
- Code plus concis et maintenable
- Ajout de la liste des ingrédients pour le formulaire d'ajout manuel
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from models.models import db, ListeCourses, Ingredient
from utils.database import db_transaction_with_flash
from utils.calculs import calculer_budget_courses
from utils.forms import parse_positive_float, parse_checkbox
from utils.stock import ajouter_au_stock
from utils.queries import get_courses_non_achetees, get_course_by_ingredient

courses_bp = Blueprint('courses', __name__)


@courses_bp.route('/', methods=['GET', 'POST'])
def liste():
    """
    Liste de courses avec possibilité de marquer les articles comme achetés
    """
    if request.method == 'POST':
        try:
            # ✅ REFACTORISÉ: Requête centralisée
            items = get_courses_non_achetees()
            
            if not items:
                flash('Aucun article à valider dans la liste de courses.', 'info')
                return redirect(url_for('courses.liste'))
            
            items_valides = 0
            erreurs = []
            
            for item in items:
                checkbox_name = f'achete_{item.id}'
                quantite_name = f'quantite_{item.id}'
                
                # Vérifier si l'article est coché
                est_achete = parse_checkbox(request.form.get(checkbox_name))
                
                if est_achete:
                    try:
                        # Récupérer la quantité achetée
                        quantite_achetee = parse_positive_float(
                            request.form.get(quantite_name, item.quantite)
                        )
                        
                        # ✅ REFACTORISÉ: Utilisation de utils/stock.py
                        ajouter_au_stock(item.ingredient_id, quantite_achetee)
                        
                        # Marquer comme acheté
                        item.achete = True
                        items_valides += 1
                        
                    except Exception as e:
                        erreurs.append(f'{item.ingredient.nom}: {str(e)}')
            
            # Commit des changements
            db.session.commit()
            
            if items_valides > 0:
                flash(
                    f'✓ {items_valides} article(s) validé(s) et ajouté(s) au frigo !',
                    'success'
                )
            
            if erreurs:
                for erreur in erreurs[:5]:
                    flash(f'⚠️ {erreur}', 'warning')
                
                if len(erreurs) > 5:
                    flash(f'... et {len(erreurs) - 5} autre(s) erreur(s)', 'warning')
            
            if items_valides == 0 and not erreurs:
                flash('Aucun article sélectionné.', 'info')
        
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Erreur dans courses.liste (POST): {str(e)}')
            flash('Une erreur est survenue lors de la validation des courses.', 'danger')
        
        return redirect(url_for('courses.liste'))
    
    # ============================================
    # GET - AFFICHAGE DE LA LISTE
    # ============================================
    
    try:
        # ✅ REFACTORISÉ: Requêtes centralisées
        items = get_courses_non_achetees()
        
        # Calcul du budget (déjà centralisé)
        budget = calculer_budget_courses(items)
        
        # Liste des ingrédients pour le formulaire d'ajout manuel
        all_ingredients = Ingredient.query.order_by(Ingredient.nom).all()
        
        return render_template(
            'courses.html',
            items=items,
            total_estime=budget.total_estime,
            items_avec_prix=budget.items_avec_prix,
            items_sans_prix=budget.items_sans_prix,
            all_ingredients=all_ingredients
        )
    
    except Exception as e:
        current_app.logger.error(f'Erreur dans courses.liste (GET): {str(e)}')
        flash('Erreur lors du chargement de la liste de courses.', 'danger')
        return render_template(
            'courses.html', 
            items=[], 
            total_estime=0,
            items_avec_prix=0,
            items_sans_prix=0,
            all_ingredients=[]
        )


@courses_bp.route('/retirer/<int:id>')
def retirer(id):
    """
    Retirer un article de la liste de courses
    """
    try:
        item = ListeCourses.query.get_or_404(id)
        nom = item.ingredient.nom
        
        with db_transaction_with_flash(
            success_message=f'✓ {nom} retiré de la liste de courses.',
            error_message=f'Erreur lors de la suppression de {nom}'
        ):
            db.session.delete(item)
        
        current_app.logger.info(f'Article retiré de la liste: {nom}')
    
    except Exception as e:
        current_app.logger.error(f'Erreur dans courses.retirer: {str(e)}')
        flash('Erreur lors de la suppression de l\'article.', 'danger')
    
    return redirect(url_for('courses.liste'))


@courses_bp.route('/vider-historique')
def vider_historique():
    """
    Vider l'historique des courses achetées
    """
    try:
        # Compter les items à supprimer
        items_achetes = ListeCourses.query.filter_by(achete=True).all()
        nb_items = len(items_achetes)
        
        if nb_items == 0:
            flash('L\'historique est déjà vide.', 'info')
            return redirect(url_for('courses.liste'))
        
        with db_transaction_with_flash(
            success_message=f'✓ {nb_items} article(s) supprimé(s) de l\'historique.',
            error_message='Erreur lors du vidage de l\'historique'
        ):
            for item in items_achetes:
                db.session.delete(item)
        
        current_app.logger.info(f'Historique des courses vidé: {nb_items} items')
    
    except Exception as e:
        current_app.logger.error(f'Erreur dans courses.vider_historique: {str(e)}')
        flash('Erreur lors du vidage de l\'historique.', 'danger')
    
    return redirect(url_for('courses.liste'))


@courses_bp.route('/ajouter', methods=['POST'])
def ajouter():
    """
    Ajouter manuellement un article à la liste de courses
    """
    try:
        ingredient_id = request.form.get('ingredient_id')
        quantite = parse_positive_float(request.form.get('quantite', 1))
        
        if not ingredient_id:
            flash('Veuillez sélectionner un ingrédient.', 'danger')
            return redirect(url_for('courses.liste'))
        
        ingredient = Ingredient.query.get_or_404(ingredient_id)
        
        # Vérifier si l'ingrédient est déjà dans la liste
        existing = get_course_by_ingredient(int(ingredient_id), achete=False)
        
        if existing:
            # Augmenter la quantité
            existing.quantite += quantite
            flash(
                f'✓ Quantité de {ingredient.nom} augmentée à {existing.quantite} {ingredient.unite}',
                'success'
            )
        else:
            # Ajouter nouveau
            item = ListeCourses(
                ingredient_id=int(ingredient_id),
                quantite=quantite
            )
            db.session.add(item)
            flash(f'✓ {ingredient.nom} ajouté à la liste de courses.', 'success')
        
        db.session.commit()
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Erreur dans courses.ajouter: {str(e)}')
        flash('Erreur lors de l\'ajout de l\'article.', 'danger')
    
    return redirect(url_for('courses.liste'))
