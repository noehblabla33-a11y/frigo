"""
routes/frigo.py (VERSION REFACTORISÉE - CORRIGÉE)
Gestion du stock du frigo

CHANGEMENTS:
- Utilise utils/stock.py pour les opérations sur le stock
- Code plus concis et maintenable
- ✅ CORRIGÉ: Ajout de valeur_totale_globale pour le template
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from models.models import db, Ingredient
from utils.database import db_transaction_with_flash
from utils.pagination import paginate_query
from utils.forms import parse_float, parse_positive_float
# ✅ NOUVEAUX IMPORTS
from utils.stock import (
    ajouter_au_stock, 
    retirer_du_stock, 
    definir_stock, 
    supprimer_du_frigo,
    get_stocks_avec_ingredients,
    get_quantite_disponible
)

frigo_bp = Blueprint('frigo', __name__)


def calculer_valeur_totale_stock(stocks):
    """
    Calcule la valeur totale du stock.
    
    Args:
        stocks: Liste de StockFrigo avec ingrédients préchargés
    
    Returns:
        float: Valeur totale en euros
    """
    total = 0
    for stock in stocks:
        if stock.ingredient.prix_unitaire and stock.ingredient.prix_unitaire > 0:
            total += stock.quantite * stock.ingredient.prix_unitaire
    return total


@frigo_bp.route('/', methods=['GET', 'POST'])
def liste():
    """
    Gestion du stock du frigo avec ajout/retrait/définition de quantités
    """
    if request.method == 'POST':
        try:
            ingredient_id = request.form.get('ingredient_id')
            action = request.form.get('action', 'set')

            if not ingredient_id:
                flash('Aucun ingrédient sélectionné.', 'danger')
                return redirect(url_for('frigo.liste'))

            quantite = parse_positive_float(request.form.get('quantite'))
            
            # Récupérer l'ingrédient
            ingredient = Ingredient.query.get_or_404(ingredient_id)
            
            # ✅ REFACTORISÉ: Utilisation de utils/stock.py
            try:
                if action == 'add':
                    stock, nouvelle_quantite = ajouter_au_stock(int(ingredient_id), quantite)
                    if nouvelle_quantite == quantite:
                        message_success = f'✓ {ingredient.nom} ajouté au frigo : {quantite} {ingredient.unite}'
                    else:
                        message_success = (
                            f'✓ {quantite} {ingredient.unite} de {ingredient.nom} ajouté(s) ! '
                            f'Total : {nouvelle_quantite} {ingredient.unite}'
                        )
                
                elif action == 'remove':
                    stock, nouvelle_quantite = retirer_du_stock(int(ingredient_id), quantite)
                    if stock is None:
                        flash(f'{ingredient.nom} n\'est pas dans le frigo !', 'warning')
                        return redirect(url_for('frigo.liste'))
                    message_success = (
                        f'✓ {quantite} {ingredient.unite} de {ingredient.nom} retiré(s) ! '
                        f'Reste : {nouvelle_quantite} {ingredient.unite}'
                    )
                
                else:  # action == 'set'
                    stock = definir_stock(int(ingredient_id), quantite)
                    if stock:
                        message_success = f'✓ Stock de {ingredient.nom} mis à jour : {quantite} {ingredient.unite}'
                    else:
                        message_success = f'✓ {ingredient.nom} retiré du frigo.'
                
                db.session.commit()
                flash(message_success, 'success')
                
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f'Erreur stock: {str(e)}')
                flash('Erreur lors de la mise à jour du stock.', 'danger')
        
        except ValueError as e:
            flash(str(e), 'danger')
        
        return redirect(url_for('frigo.liste'))
    
    # ============================================
    # GET - AFFICHAGE DU STOCK
    # ============================================
    
    try:
        page = request.args.get('page', 1, type=int)
        view_mode = request.args.get('view', 'list')
        items_per_page = current_app.config.get('ITEMS_PER_PAGE_DEFAULT', 24)
        
        # ✅ REFACTORISÉ: Utilisation de utils/stock.py
        # Récupère TOUS les stocks pour calculer la valeur totale
        tous_les_stocks = get_stocks_avec_ingredients(order_by='nom')
        
        # ✅ CORRIGÉ: Calculer la valeur totale GLOBALE (toutes pages)
        valeur_totale_globale = calculer_valeur_totale_stock(tous_les_stocks)
        
        # Pagination manuelle
        total = len(tous_les_stocks)
        pages = (total + items_per_page - 1) // items_per_page if total > 0 else 1
        page = min(max(1, page), pages)
        start = (page - 1) * items_per_page
        end = start + items_per_page
        
        pagination = {
            'items': tous_les_stocks[start:end],
            'total': total,
            'page': page,
            'pages': pages,
            'per_page': items_per_page,
            'has_prev': page > 1,
            'has_next': page < pages,
            'prev_page': page - 1 if page > 1 else None,
            'next_page': page + 1 if page < pages else None
        }
        
        # Récupérer tous les ingrédients pour le formulaire d'ajout
        tous_ingredients = Ingredient.query.order_by(Ingredient.nom).all()
        
        # ✅ CORRIGÉ: Passer valeur_totale_globale et view_mode au template
        return render_template(
            'frigo.html', 
            stocks=pagination['items'],
            pagination=pagination,
            tous_ingredients=tous_ingredients,
            valeur_totale_globale=valeur_totale_globale,  # ✅ AJOUTÉ
            view_mode=view_mode  # ✅ AJOUTÉ (utilisé dans pagination)
        )
    
    except Exception as e:
        current_app.logger.error(f'Erreur dans frigo.liste (GET): {str(e)}')
        flash('Erreur lors du chargement du stock.', 'danger')
        return render_template(
            'frigo.html', 
            stocks=[], 
            pagination={
                'items': [], 'total': 0, 'page': 1, 'pages': 1,
                'per_page': 24, 'has_prev': False, 'has_next': False,
                'prev_page': None, 'next_page': None
            },
            tous_ingredients=[],
            valeur_totale_globale=0,  # ✅ AJOUTÉ
            view_mode='list'  # ✅ AJOUTÉ
        )


@frigo_bp.route('/retirer/<int:id>')
def retirer(id):
    """
    Retire complètement un ingrédient du frigo
    """
    ingredient = Ingredient.query.get_or_404(id)
    nom = ingredient.nom
    
    # ✅ REFACTORISÉ: Utilisation de utils/stock.py
    with db_transaction_with_flash(
        success_message=f'✓ {nom} retiré du frigo.',
        error_message=f'Erreur lors du retrait de {nom}'
    ):
        if not supprimer_du_frigo(id):
            flash(f'{nom} n\'est pas dans le frigo !', 'warning')
    
    return redirect(url_for('frigo.liste'))


@frigo_bp.route('/vider/<int:id>')
def vider(id):
    """
    Vider complètement un article du frigo (par stock_id)
    Note: Cette route utilise l'ID du stock, pas de l'ingrédient
    """
    from models.models import StockFrigo
    
    try:
        stock = StockFrigo.query.get_or_404(id)
        nom = stock.ingredient.nom
        
        with db_transaction_with_flash(
            success_message=f'✓ {nom} retiré du frigo !',
            error_message='Erreur lors de la suppression'
        ):
            db.session.delete(stock)
        
        current_app.logger.info(f'Stock vidé: {nom}')
    
    except Exception as e:
        current_app.logger.error(f'Erreur dans frigo.vider: {str(e)}')
        flash('Erreur lors de la suppression.', 'danger')
    
    return redirect(url_for('frigo.liste'))


@frigo_bp.route('/vider-tout')
def vider_tout():
    """
    Vide complètement le frigo
    """
    from utils.stock import vider_frigo
    
    with db_transaction_with_flash(
        success_message='✓ Le frigo a été vidé.',
        error_message='Erreur lors du vidage du frigo'
    ):
        count = vider_frigo()
        if count > 0:
            flash(f'{count} ingrédient(s) retiré(s).', 'info')
    
    return redirect(url_for('frigo.liste'))


# ============================================
# API JSON
# ============================================

@frigo_bp.route('/api/stock/<int:ingredient_id>')
def api_get_stock(ingredient_id):
    """
    Retourne le stock d'un ingrédient (API JSON)
    """
    # ✅ REFACTORISÉ: Utilisation de utils/stock.py
    quantite = get_quantite_disponible(ingredient_id)
    ingredient = Ingredient.query.get(ingredient_id)
    
    if not ingredient:
        return jsonify({'error': 'Ingrédient non trouvé'}), 404
    
    return jsonify({
        'ingredient_id': ingredient_id,
        'ingredient_nom': ingredient.nom,
        'quantite': quantite,
        'unite': ingredient.unite
    })


@frigo_bp.route('/api/stock', methods=['POST'])
def api_update_stock():
    """
    Met à jour le stock via API JSON
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Données manquantes'}), 400
    
    ingredient_id = data.get('ingredient_id')
    quantite = data.get('quantite', 0)
    action = data.get('action', 'set')
    
    if not ingredient_id:
        return jsonify({'error': 'ingredient_id requis'}), 400
    
    try:
        # ✅ REFACTORISÉ: Utilisation de utils/stock.py
        if action == 'add':
            stock, nouvelle_quantite = ajouter_au_stock(ingredient_id, quantite)
        elif action == 'remove':
            stock, nouvelle_quantite = retirer_du_stock(ingredient_id, quantite)
        else:
            stock = definir_stock(ingredient_id, quantite)
            nouvelle_quantite = quantite if stock else 0
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'ingredient_id': ingredient_id,
            'nouvelle_quantite': nouvelle_quantite,
            'action': action
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@frigo_bp.route('/api/stock/update', methods=['POST'])
def api_update_quantite():
    """
    Met à jour la quantité d'un stock existant (utilisé par l'édition inline)
    """
    from models.models import StockFrigo
    
    data = request.get_json()
    
    if not data:
        return jsonify({'success': False, 'error': 'Données manquantes'}), 400
    
    stock_id = data.get('stock_id')
    nouvelle_quantite = data.get('quantite')
    
    if stock_id is None or nouvelle_quantite is None:
        return jsonify({'success': False, 'error': 'stock_id et quantite requis'}), 400
    
    try:
        stock = StockFrigo.query.get(stock_id)
        
        if not stock:
            return jsonify({'success': False, 'error': 'Stock non trouvé'}), 404
        
        if nouvelle_quantite <= 0:
            # Si quantité <= 0, supprimer le stock
            db.session.delete(stock)
            db.session.commit()
            return jsonify({
                'success': True,
                'deleted': True,
                'message': f'{stock.ingredient.nom} retiré du frigo'
            })
        
        stock.quantite = nouvelle_quantite
        db.session.commit()
        
        return jsonify({
            'success': True,
            'stock_id': stock_id,
            'nouvelle_quantite': nouvelle_quantite,
            'ingredient_nom': stock.ingredient.nom
        })
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Erreur API update stock: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 500
