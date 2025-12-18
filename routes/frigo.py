"""
routes/frigo.py
Gestion du stock du frigo

✅ VERSION OPTIMISÉE - PHASE 2
- Utilise utils/pagination.py (pas de duplication)
- Transactions sécurisées
- Gestion d'erreurs robuste
- Logs appropriés
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from models.models import db, Ingredient, StockFrigo
from utils.database import db_transaction_with_flash, db_transaction
from utils.pagination import paginate_query  # ✅ Import depuis utils
from sqlalchemy.orm import joinedload

frigo_bp = Blueprint('frigo', __name__)


@frigo_bp.route('/', methods=['GET', 'POST'])
def liste():
    """
    Gestion du stock du frigo avec ajout/retrait/définition de quantités
    """
    if request.method == 'POST':
        try:
            ingredient_id = request.form.get('ingredient_id')
            quantite_str = request.form.get('quantite', '0').strip()
            action = request.form.get('action', 'set')
            
            # ✅ VALIDATION
            if not ingredient_id:
                flash('Aucun ingrédient sélectionné.', 'danger')
                return redirect(url_for('frigo.liste'))
            
            try:
                quantite = float(quantite_str)
                if quantite < 0:
                    flash('La quantité ne peut pas être négative.', 'danger')
                    return redirect(url_for('frigo.liste'))
            except ValueError:
                flash('Format de quantité invalide.', 'danger')
                return redirect(url_for('frigo.liste'))
            
            # Récupérer l'ingrédient
            ingredient = Ingredient.query.get_or_404(ingredient_id)
            stock = StockFrigo.query.filter_by(ingredient_id=ingredient_id).first()
            
            # ✅ TRANSACTION SÉCURISÉE
            try:
                # Préparer le message selon l'action
                if action == 'add':
                    if stock:
                        nouvelle_quantite = stock.quantite + quantite
                        message_success = (
                            f'✓ {quantite} {ingredient.unite} de {ingredient.nom} ajouté(s) ! '
                            f'Total : {nouvelle_quantite} {ingredient.unite}'
                        )
                    else:
                        nouvelle_quantite = quantite
                        message_success = f'✓ {ingredient.nom} ajouté au frigo : {quantite} {ingredient.unite}'
                
                elif action == 'remove':
                    if stock:
                        nouvelle_quantite = max(0, stock.quantite - quantite)
                        message_success = (
                            f'✓ {quantite} {ingredient.unite} de {ingredient.nom} retiré(s) ! '
                            f'Reste : {nouvelle_quantite} {ingredient.unite}'
                        )
                    else:
                        flash(f'{ingredient.nom} n\'est pas dans le frigo !', 'danger')
                        return redirect(url_for('frigo.liste'))
                
                else:  # set
                    nouvelle_quantite = quantite
                    message_success = f'✓ {ingredient.nom} mis à jour : {quantite} {ingredient.unite}'
                
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
                
                current_app.logger.info(
                    f'Stock mis à jour: {ingredient.nom} - '
                    f'action={action}, quantite={quantite}'
                )
            
            except Exception:
                pass  # Géré par le context manager
        
        except Exception as e:
            current_app.logger.error(f'Erreur dans frigo.liste (POST): {str(e)}')
            flash('Une erreur est survenue lors de la mise à jour du stock.', 'danger')
        
        return redirect(url_for('frigo.liste'))
    
    # ============================================
    # GET - AFFICHAGE DU STOCK
    # ============================================
    
    try:
        page = request.args.get('page', 1, type=int)
        
        # ✅ OPTIMISATION : Filtrer les stocks > 0 au niveau SQL + charger les ingrédients
        query = (
            StockFrigo.query
            .options(joinedload(StockFrigo.ingredient))
            .join(Ingredient)
            .filter(StockFrigo.quantite > 0)
            .order_by(Ingredient.nom)
        )
        
        # ✅ UTILISATION DE LA FONCTION CENTRALISÉE (pas de duplication)
        pagination = paginate_query(query, page)  # per_page depuis config
        
        # Tous les ingrédients pour le formulaire d'ajout
        tous_ingredients = Ingredient.query.order_by(Ingredient.nom).all()
        
        # ✅ Calculer la valeur totale de TOUS les stocks (toutes pages)
        valeur_totale_globale = 0
        tous_les_stocks = query.all()
        
        for stock in tous_les_stocks:
            if stock.ingredient.prix_unitaire and stock.ingredient.prix_unitaire > 0:
                valeur_totale_globale += stock.quantite * stock.ingredient.prix_unitaire
        
        return render_template(
            'frigo.html',
            stocks=pagination['items'],
            pagination=pagination,
            tous_ingredients=tous_ingredients,
            valeur_totale_globale=valeur_totale_globale
        )
    
    except Exception as e:
        current_app.logger.error(f'Erreur dans frigo.liste (GET): {str(e)}')
        flash('Erreur lors du chargement du stock.', 'danger')
        return render_template('frigo.html', stocks=[], tous_ingredients=[], pagination={})


@frigo_bp.route('/vider/<int:id>')
def vider(id):
    """
    Vider complètement un article du frigo
    """
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


@frigo_bp.route('/update-quantite/<int:stock_id>', methods=['POST'])
def update_quantite(stock_id):
    """
    Mise à jour rapide de la quantité en AJAX
    
    Utilisé pour les modifications en direct depuis le tableau
    """
    try:
        stock = StockFrigo.query.get_or_404(stock_id)
        
        # Récupérer la nouvelle quantité depuis le JSON
        data = request.get_json()
        nouvelle_quantite = float(data.get('quantite', 0))
        
        # ✅ VALIDATION
        if nouvelle_quantite < 0:
            return jsonify({
                'success': False,
                'message': 'La quantité ne peut pas être négative'
            }), 400
        
        # ✅ TRANSACTION SÉCURISÉE (sans flash pour AJAX)
        with db_transaction():
            stock.quantite = nouvelle_quantite
        
        current_app.logger.info(
            f'Stock mis à jour via AJAX: {stock.ingredient.nom} = {nouvelle_quantite}'
        )
        
        return jsonify({
            'success': True,
            'message': f'{stock.ingredient.nom} mis à jour',
            'quantite': stock.quantite,
            'unite': stock.ingredient.unite
        })
    
    except ValueError:
        return jsonify({
            'success': False,
            'message': 'Format de quantité invalide'
        }), 400
    
    except Exception as e:
        current_app.logger.error(f'Erreur dans frigo.update_quantite: {str(e)}')
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
