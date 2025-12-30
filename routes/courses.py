"""
routes/courses.py (VERSION CORRIGÉE)
Gestion de la liste de courses

✅ CORRIGÉ :
- Nettoyage automatique des items orphelins au chargement
- Import de nettoyer_courses_orphelines depuis utils/queries.py
- Meilleure gestion des erreurs avec logs détaillés
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from models.models import db, ListeCourses, Ingredient
from utils.database import db_transaction_with_flash
from utils.calculs import calculer_budget_courses
from utils.forms import parse_positive_float, parse_checkbox
from utils.stock import ajouter_au_stock
from utils.queries import get_courses_non_achetees, get_course_by_ingredient, nettoyer_courses_orphelines

courses_bp = Blueprint('courses', __name__)


@courses_bp.route('/', methods=['GET', 'POST'])
def liste():
    """
    Liste de courses avec possibilité de marquer les articles comme achetés
    """
    if request.method == 'POST':
        try:
            items = get_courses_non_achetees()
            
            if not items:
                flash('Aucun article à valider dans la liste de courses.', 'info')
                return redirect(url_for('courses.liste'))
            
            items_valides = 0
            erreurs = []
            
            for item in items:
                checkbox_name = f'achete_{item.id}'
                quantite_name = f'quantite_{item.id}'
                
                est_achete = parse_checkbox(request.form.get(checkbox_name))
                
                if est_achete:
                    try:
                        quantite_achetee = parse_positive_float(
                            request.form.get(quantite_name, item.quantite)
                        )
                        
                        ajouter_au_stock(item.ingredient_id, quantite_achetee)
                        item.achete = True
                        items_valides += 1
                        
                    except Exception as e:
                        erreurs.append(f'{item.ingredient.nom}: {str(e)}')
            
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
        # ✅ NOUVEAU : Nettoyer les items orphelins avant le chargement
        nb_orphelins = nettoyer_courses_orphelines()
        if nb_orphelins > 0:
            current_app.logger.warning(
                f'Nettoyage automatique: {nb_orphelins} item(s) orphelin(s) supprimé(s) de la liste de courses'
            )
        
        # Requête centralisée (maintenant filtre les orphelins via INNER JOIN)
        items = get_courses_non_achetees()
        
        # Calcul du budget
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
        current_app.logger.error(f'Erreur dans courses.liste (GET): {str(e)}', exc_info=True)
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
        
        # ✅ CORRIGÉ : Vérifier que l'ingrédient existe
        if item.ingredient:
            nom = item.ingredient.nom
        else:
            nom = f"Article #{id}"
        
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


@courses_bp.route('/vider')
def vider():
    """
    Vider complètement la liste de courses (items non achetés)
    """
    try:
        items = ListeCourses.query.filter_by(achete=False).all()
        nb_items = len(items)
        
        if nb_items == 0:
            flash('La liste de courses est déjà vide.', 'info')
            return redirect(url_for('courses.liste'))
        
        with db_transaction_with_flash(
            success_message=f'✓ {nb_items} article(s) supprimé(s) de la liste.',
            error_message='Erreur lors du vidage de la liste'
        ):
            for item in items:
                db.session.delete(item)
        
        current_app.logger.info(f'Liste de courses vidée: {nb_items} items')
    
    except Exception as e:
        current_app.logger.error(f'Erreur dans courses.vider: {str(e)}')
        flash('Erreur lors du vidage de la liste.', 'danger')
    
    return redirect(url_for('courses.liste'))


@courses_bp.route('/vider-historique')
def vider_historique():
    """
    Vider l'historique des courses achetées
    """
    try:
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
        
        # ✅ IMPORTANT : Vérifier que l'ingrédient existe
        ingredient = Ingredient.query.get(ingredient_id)
        if not ingredient:
            flash('Ingrédient non trouvé.', 'danger')
            return redirect(url_for('courses.liste'))
        
        # Vérifier si l'ingrédient est déjà dans la liste
        existing = get_course_by_ingredient(int(ingredient_id), achete=False)
        
        if existing:
            existing.quantite += quantite
            flash(
                f'✓ Quantité de {ingredient.nom} augmentée à {existing.quantite} {ingredient.unite}',
                'success'
            )
        else:
            item = ListeCourses(
                ingredient_id=int(ingredient_id),
                quantite=quantite
            )
            db.session.add(item)
            flash(f'✓ {ingredient.nom} ajouté à la liste de courses.', 'success')
        
        db.session.commit()
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Erreur dans courses.ajouter: {str(e)}', exc_info=True)
        flash('Erreur lors de l\'ajout de l\'article.', 'danger')
    
    return redirect(url_for('courses.liste'))


@courses_bp.route('/nettoyer')
def nettoyer():
    """
    Route manuelle pour nettoyer les items orphelins
    """
    try:
        nb_orphelins = nettoyer_courses_orphelines()
        
        if nb_orphelins > 0:
            flash(f'✓ {nb_orphelins} article(s) orphelin(s) supprimé(s).', 'success')
        else:
            flash('Aucun article orphelin trouvé.', 'info')
    
    except Exception as e:
        current_app.logger.error(f'Erreur dans courses.nettoyer: {str(e)}')
        flash('Erreur lors du nettoyage.', 'danger')
    
    return redirect(url_for('courses.liste'))
