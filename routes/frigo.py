from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from sqlalchemy.orm import joinedload
from models.models import db, Ingredient, StockFrigo
from utils.database import db_transaction_with_flash, paginate_query
from utils.forms import parse_float, parse_positive_float
from utils.stock import (
    ajouter_au_stock, 
    retirer_du_stock, 
    definir_stock,
    get_quantite_disponible
)
from utils.queries import get_stocks_with_ingredients

frigo_bp = Blueprint('frigo', __name__)


def calculer_valeur_totale_stock(stocks):
    """
    Calcule la valeur totale du stock.

    Paramètres:
        stocks: Liste de StockFrigo avec ingrédients préchargés

    Retour:
        float: Valeur totale en euros
    """
    return round(sum(
        stock.ingredient.calculer_prix(stock.quantite)
        for stock in stocks
    ), 2)


def _appliquer_action_stock(ingredient_id, action, quantite):
    """
    Applique une action sur le stock d'un ingrédient.

    Paramètres:
        ingredient_id: ID de l'ingrédient
        action: 'add', 'remove' ou 'set'
        quantite: Quantité concernée

    Retour:
        str: Message de succès
    """
    ingredient = Ingredient.query.get_or_404(ingredient_id)

    if action == 'add':
        stock, nouvelle_quantite = ajouter_au_stock(int(ingredient_id), quantite)
        if nouvelle_quantite == quantite:
            return f'✓ {ingredient.nom} ajouté au frigo : {quantite} {ingredient.unite}'
        return (
            f'✓ {quantite} {ingredient.unite} de {ingredient.nom} ajouté(s) ! '
            f'Total : {nouvelle_quantite} {ingredient.unite}'
        )

    elif action == 'remove':
        stock, nouvelle_quantite = retirer_du_stock(int(ingredient_id), quantite)
        if stock is None:
            raise ValueError(f'{ingredient.nom} n\'est pas dans le frigo !')
        if nouvelle_quantite <= 0:
            raise ValueError(f'⚠️ Stock de {ingredient.nom} épuisé !')
        return (
            f'✓ {quantite} {ingredient.unite} de {ingredient.nom} retiré(s) ! '
            f'Reste : {nouvelle_quantite} {ingredient.unite}'
        )

    else:
        definir_stock(int(ingredient_id), quantite)
        return f'✓ Stock de {ingredient.nom} défini à {quantite} {ingredient.unite}'


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

            with db_transaction_with_flash(
                success_message=None,
                error_message='Erreur lors de la mise à jour du stock.'
            ):
                message = _appliquer_action_stock(ingredient_id, action, quantite)
                flash(message, 'success')

        except (ValueError, TypeError) as e:
            flash(str(e), 'warning')

        return redirect(url_for('frigo.liste'))
    
    # ============================================
    # GET - AFFICHAGE DU STOCK
    # ============================================
    
    try:
        page = request.args.get('page', 1, type=int)
        view_mode = request.args.get('view', 'list')
        items_per_page = current_app.config.get('ITEMS_PER_PAGE_DEFAULT', 24)
        
        # Récupère TOUS les stocks pour calculer la valeur totale
        tous_les_stocks = get_stocks_with_ingredients(order_by='nom')
        
        # ✅ CORRIGÉ: Calculer la valeur totale avec la méthode corrigée
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
        
        # ✅ CORRIGÉ: Récupérer tous les ingrédients AVEC leur stock préchargé
        tous_ingredients = Ingredient.query.options(
            joinedload(Ingredient.stock)
        ).order_by(Ingredient.nom).all()
        
        # Log pour debug
        current_app.logger.info(f'Frigo: {len(tous_ingredients)} ingrédients chargés pour le formulaire')
        
        return render_template(
            'frigo.html', 
            stocks=pagination['items'],
            pagination=pagination,
            tous_ingredients=tous_ingredients,
            valeur_totale=valeur_totale_globale,  # ✅ Renommé pour correspondre au template
            valeur_totale_globale=valeur_totale_globale,  # Garder pour compatibilité
            view_mode=view_mode
        )
    
    except Exception as e:
        current_app.logger.error(f'Erreur dans frigo.liste (GET): {str(e)}')
        import traceback
        current_app.logger.error(traceback.format_exc())
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
            valeur_totale=0,
            valeur_totale_globale=0,
            view_mode='list'
        )


@frigo_bp.route('/supprimer/<int:stock_id>')
def supprimer(stock_id):
    """
    Supprime un stock du frigo par son ID.

    Paramètres:
        stock_id: ID de l'entrée StockFrigo
    """
    stock = StockFrigo.query.get_or_404(stock_id)
    nom = stock.ingredient.nom

    with db_transaction_with_flash(
        success_message=f'✓ {nom} retiré du frigo !',
        error_message=f'Erreur lors de la suppression de {nom}'
    ):
        db.session.delete(stock)

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


@frigo_bp.route('/update-quantite/<int:stock_id>', methods=['POST'])
def update_quantite(stock_id):
    """
    API AJAX pour mise à jour rapide de la quantité.

    Paramètres:
        stock_id: ID de l'entrée StockFrigo
    """
    try:
        data = request.get_json()
        nouvelle_quantite = float(data.get('quantite', 0))

        if nouvelle_quantite < 0:
            return jsonify({'success': False, 'message': 'La quantité ne peut pas être négative'}), 400

        stock = StockFrigo.query.get_or_404(stock_id)
        result = definir_stock(stock.ingredient_id, nouvelle_quantite)

        db.session.commit()

        deleted = result is None
        return jsonify({
            'success': True,
            'quantite': 0 if deleted else result.quantite,
            'deleted': deleted,
            'message': 'Stock supprimé' if deleted else 'Quantité mise à jour'
        })

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Erreur update_quantite: {str(e)}')
        return jsonify({'success': False, 'message': str(e)}), 500
