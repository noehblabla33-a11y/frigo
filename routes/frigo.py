"""
routes/frigo.py - VERSION OPTIMISÉE AVEC CONTEXT MANAGERS
Gestion du stock du frigo avec transactions sécurisées
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from models.models import db, Ingredient, StockFrigo

# ✅ Imports des utilitaires optimisés
from utils.database import db_transaction_with_flash

frigo_bp = Blueprint('frigo', __name__)

# Nombre d'éléments par page
ITEMS_PER_PAGE = 24

def paginate_query(query, page, per_page=ITEMS_PER_PAGE):
    """Helper de pagination"""
    page = max(1, page)
    total = query.count()
    pages = (total + per_page - 1) // per_page if total > 0 else 1
    page = min(page, pages)
    items = query.limit(per_page).offset((page - 1) * per_page).all()
    
    return {
        'items': items,
        'total': total,
        'page': page,
        'pages': pages,
        'per_page': per_page,
        'has_prev': page > 1,
        'has_next': page < pages,
        'prev_page': page - 1 if page > 1 else None,
        'next_page': page + 1 if page < pages else None
    }


@frigo_bp.route('/', methods=['GET', 'POST'])
def liste():
    if request.method == 'POST':
        ingredient_id = request.form.get('ingredient_id')
        quantite = float(request.form.get('quantite', 0))
        action = request.form.get('action', 'set')
        
        ingredient = Ingredient.query.get_or_404(ingredient_id)
        stock = StockFrigo.query.filter_by(ingredient_id=ingredient_id).first()
        
        # ✅ TRANSACTION SÉCURISÉE pour mettre à jour le stock
        try:
            # Préparer le message selon l'action
            if action == 'add':
                if stock:
                    nouvelle_quantite = stock.quantite + quantite
                    message_success = f'{quantite} {ingredient.unite} de {ingredient.nom} ajouté(s) ! Total : {nouvelle_quantite} {ingredient.unite}'
                else:
                    message_success = f'{ingredient.nom} ajouté au frigo : {quantite} {ingredient.unite}'
            
            elif action == 'remove':
                if stock:
                    nouvelle_quantite = max(0, stock.quantite - quantite)
                    message_success = f'{quantite} {ingredient.unite} de {ingredient.nom} retiré(s) ! Reste : {nouvelle_quantite} {ingredient.unite}'
                else:
                    flash(f'{ingredient.nom} n\'est pas dans le frigo !', 'danger')
                    return redirect(url_for('frigo.liste'))
            
            else:  # set
                message_success = f'{ingredient.nom} mis à jour : {quantite} {ingredient.unite}'
            
            # Transaction avec le message approprié
            with db_transaction_with_flash(
                success_message=message_success,
                error_message='Erreur lors de la mise à jour du stock'
            ):
                if action == 'add':
                    if stock:
                        stock.quantite += quantite
                    else:
                        stock = StockFrigo(ingredient_id=ingredient_id, quantite=quantite)
                        db.session.add(stock)
                
                elif action == 'remove':
                    stock.quantite = max(0, stock.quantite - quantite)
                
                else:  # set
                    if stock:
                        stock.quantite = quantite
                    else:
                        stock = StockFrigo(ingredient_id=ingredient_id, quantite=quantite)
                        db.session.add(stock)
        
        except Exception:
            pass
        
        return redirect(url_for('frigo.liste'))
    
    # ============================================
    # AFFICHAGE DE LA LISTE (GET)
    # ============================================
    
    view_mode = request.args.get('view', 'grid')
    page = request.args.get('page', 1, type=int)
    
    query = StockFrigo.query.join(Ingredient).order_by(Ingredient.nom)
    pagination = paginate_query(query, page, ITEMS_PER_PAGE)
    tous_ingredients = Ingredient.query.order_by(Ingredient.nom).all()
    
    return render_template('frigo.html',
                         stocks=pagination['items'],
                         pagination=pagination,
                         tous_ingredients=tous_ingredients,
                         view_mode=view_mode)


@frigo_bp.route('/vider/<int:id>')
def vider(id):
    stock = StockFrigo.query.get_or_404(id)
    nom = stock.ingredient.nom
    
    try:
        with db_transaction_with_flash(
            success_message=f'{nom} retiré du frigo !',
            error_message='Erreur lors de la suppression'
        ):
            db.session.delete(stock)
    
    except Exception:
        pass
    
    return redirect(url_for('frigo.liste'))


@frigo_bp.route('/update-quantite/<int:stock_id>', methods=['POST'])
def update_quantite(stock_id):
    """Mise à jour rapide de la quantité en AJAX"""
    stock = StockFrigo.query.get_or_404(stock_id)
    
    try:
        nouvelle_quantite = float(request.json.get('quantite', 0))
        
        if nouvelle_quantite < 0:
            return jsonify({
                'success': False,
                'message': 'La quantité ne peut pas être négative'
            }), 400
        
        # Utiliser le context manager sans flash (pour JSON)
        from utils.database import db_transaction
        
        with db_transaction():
            stock.quantite = nouvelle_quantite
        
        return jsonify({
            'success': True,
            'message': f'{stock.ingredient.nom} mis à jour',
            'quantite': stock.quantite,
            'unite': stock.ingredient.unite
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
