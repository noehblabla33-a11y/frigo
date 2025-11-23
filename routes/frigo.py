from flask import Blueprint, render_template, request, redirect, url_for, flash
from models.models import db, Ingredient, StockFrigo

frigo_bp = Blueprint('frigo', __name__)

@frigo_bp.route('/', methods=['GET', 'POST'])
def liste():
    if request.method == 'POST':
        ingredient_id = request.form.get('ingredient_id')
        quantite = float(request.form.get('quantite', 0))
        action = request.form.get('action', 'set')
        
        ingredient = Ingredient.query.get_or_404(ingredient_id)
        stock = StockFrigo.query.filter_by(ingredient_id=ingredient_id).first()
        
        if action == 'add':
            if stock:
                stock.quantite += quantite
                flash(f'{quantite} {ingredient.unite} de {ingredient.nom} ajouté(s) ! Total : {stock.quantite} {ingredient.unite}', 'success')
            else:
                stock = StockFrigo(ingredient_id=ingredient_id, quantite=quantite)
                db.session.add(stock)
                flash(f'{ingredient.nom} ajouté au frigo : {quantite} {ingredient.unite}', 'success')
        
        elif action == 'remove':
            if stock:
                stock.quantite = max(0, stock.quantite - quantite)
                flash(f'{quantite} {ingredient.unite} de {ingredient.nom} retiré(s) ! Reste : {stock.quantite} {ingredient.unite}', 'success')
            else:
                flash(f'{ingredient.nom} n\'est pas dans le frigo !', 'danger')
        
        else:  # set
            if stock:
                stock.quantite = quantite
            else:
                stock = StockFrigo(ingredient_id=ingredient_id, quantite=quantite)
                db.session.add(stock)
            flash(f'{ingredient.nom} mis à jour : {quantite} {ingredient.unite}', 'success')
        
        db.session.commit()
        return redirect(url_for('frigo.liste'))
    
    view_mode = request.args.get('view', 'grid')  # Nouveau : 'grid' ou 'list'
    
    stocks = StockFrigo.query.join(Ingredient).order_by(Ingredient.nom).all()
    tous_ingredients = Ingredient.query.order_by(Ingredient.nom).all()
    
    return render_template('frigo.html', 
                         stocks=stocks, 
                         tous_ingredients=tous_ingredients,
                         view_mode=view_mode)

@frigo_bp.route('/vider/<int:id>')
def vider(id):
    stock = StockFrigo.query.get_or_404(id)
    nom = stock.ingredient.nom
    db.session.delete(stock)
    db.session.commit()
    flash(f'{nom} retiré du frigo !', 'success')
    return redirect(url_for('frigo.liste'))

@frigo_bp.route('/update-quantite/<int:stock_id>', methods=['POST'])
def update_quantite(stock_id):
    """Mise à jour rapide de la quantité en AJAX"""
    from flask import jsonify
    
    stock = StockFrigo.query.get_or_404(stock_id)
    
    try:
        nouvelle_quantite = float(request.json.get('quantite', 0))
        if nouvelle_quantite < 0:
            return jsonify({'success': False, 'message': 'La quantité ne peut pas être négative'}), 400
        
        stock.quantite = nouvelle_quantite
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'{stock.ingredient.nom} mis à jour',
            'quantite': stock.quantite,
            'unite': stock.ingredient.unite
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
