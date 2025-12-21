"""
routes/courses.py
Gestion de la liste de courses

✅ REFACTORISÉ : Utilise utils/calculs.py pour le calcul du budget
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from models.models import db, ListeCourses, StockFrigo
from utils.database import db_transaction_with_flash
from utils.calculs import calculer_budget_courses  # ✅ NOUVEAU
from sqlalchemy.orm import joinedload
from utils.forms import parse_float, parse_positive_float, parse_checkbox

courses_bp = Blueprint('courses', __name__)


@courses_bp.route('/', methods=['GET', 'POST'])
def liste():
    """
    Liste de courses avec possibilité de marquer les articles comme achetés
    """
    if request.method == 'POST':
        try:
            # ✅ OPTIMISATION : Charger les ingrédients en une seule requête
            items = ListeCourses.query.options(
                joinedload(ListeCourses.ingredient)
            ).filter_by(achete=False).all()
            
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
                        
                        # Mettre à jour le stock du frigo
                        stock = StockFrigo.query.filter_by(
                            ingredient_id=item.ingredient_id
                        ).first()
                        
                        if stock:
                            stock.quantite += quantite_achetee
                        else:
                            stock = StockFrigo(
                                ingredient_id=item.ingredient_id,
                                quantite=quantite_achetee
                            )
                            db.session.add(stock)
                        
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
                for erreur in erreurs[:5]:  # Limiter à 5 messages d'erreur
                    flash(f'⚠️ {erreur}', 'warning')
                
                if len(erreurs) > 5:
                    flash(f'... et {len(erreurs) - 5} autre(s) erreur(s)', 'warning')
            
            if items_valides == 0 and not erreurs:
                flash('Aucun article sélectionné.', 'info')
        
        except Exception as e:
            current_app.logger.error(f'Erreur générale dans courses.liste (POST): {str(e)}')
            flash('Une erreur est survenue lors de la validation des courses.', 'danger')
        
        return redirect(url_for('courses.liste'))
    
    # ============================================
    # GET - AFFICHAGE DE LA LISTE
    # ============================================
    
    try:
        # ✅ OPTIMISATION : Charger les ingrédients en une seule requête
        items = ListeCourses.query.options(
            joinedload(ListeCourses.ingredient)
        ).filter_by(achete=False).all()
        
        # Historique des 10 derniers achats
        historique = ListeCourses.query.options(
            joinedload(ListeCourses.ingredient)
        ).filter_by(achete=True)\
         .order_by(ListeCourses.id.desc())\
         .limit(10)\
         .all()
        
        # ✅ REFACTORISÉ : Utilisation de la fonction centralisée
        budget = calculer_budget_courses(items)
        
        return render_template(
            'courses.html',
            items=items,
            historique=historique,
            total_estime=budget.total_estime,
            items_avec_prix=budget.items_avec_prix,
            items_sans_prix=budget.items_sans_prix
        )
    
    except Exception as e:
        current_app.logger.error(f'Erreur dans courses.liste (GET): {str(e)}')
        flash('Erreur lors du chargement de la liste de courses.', 'danger')
        return render_template('courses.html', items=[], historique=[])


@courses_bp.route('/retirer/<int:id>')
def retirer(id):
    """
    Retirer un article de la liste de courses
    """
    try:
        item = ListeCourses.query.get_or_404(id)
        nom = item.ingredient.nom
        
        # ✅ TRANSACTION SÉCURISÉE
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
        
        # ✅ TRANSACTION SÉCURISÉE
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
