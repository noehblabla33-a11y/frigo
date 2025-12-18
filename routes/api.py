"""
routes/api.py
API REST pour l'application Android

✅ VERSION OPTIMISÉE - PHASE 1
- Clé API chargée depuis config (pas hardcodée)
- Requêtes optimisées avec joinedload (pas de N+1)
- Gestion d'erreurs améliorée
"""
from flask import Blueprint, jsonify, request, current_app
from models.models import db, ListeCourses, StockFrigo, Ingredient
from functools import wraps
from sqlalchemy.orm import joinedload

api_bp = Blueprint('api', __name__)


def require_api_key(f):
    """
    Décorateur pour vérifier la clé API
    ✅ La clé est maintenant chargée depuis config.py
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # ✅ Récupérer la clé depuis la config de l'app
        expected_api_key = current_app.config.get('API_KEY')
        
        # Récupérer la clé depuis les headers de la requête
        api_key = request.headers.get('X-API-Key')
        
        if not api_key or api_key != expected_api_key:
            current_app.logger.warning(f'Tentative d\'accès API avec clé invalide : {api_key}')
            return jsonify({'error': 'Clé API invalide'}), 401
        
        return f(*args, **kwargs)
    return decorated_function


@api_bp.route('/health', methods=['GET'])
def health():
    """Vérifier que l'API est accessible (endpoint public)"""
    return jsonify({
        'status': 'ok',
        'message': 'API opérationnelle',
        'version': '1.0'
    })


@api_bp.route('/courses', methods=['GET'])
@require_api_key
def get_courses():
    """
    Récupérer la liste des courses à faire
    ✅ OPTIMISÉ : Utilise joinedload pour éviter les requêtes N+1
    """
    try:
        # ✅ AVANT : items = ListeCourses.query.filter_by(achete=False).all()
        # ❌ Causait une requête SQL par item pour accéder à item.ingredient
        
        # ✅ APRÈS : Charge les ingrédients en une seule requête
        items = ListeCourses.query.options(
            joinedload(ListeCourses.ingredient)
        ).filter_by(achete=False).all()
        
        courses_list = []
        total_estime = 0
        
        for item in items:
            # Maintenant item.ingredient est déjà chargé, pas de requête supplémentaire !
            prix_estime = item.quantite * (item.ingredient.prix_unitaire or 0)
            total_estime += prix_estime
            
            courses_list.append({
                'id': item.id,
                'ingredient_id': item.ingredient_id,
                'ingredient_nom': item.ingredient.nom,
                'quantite': item.quantite,
                'unite': item.ingredient.unite,
                'prix_unitaire': item.ingredient.prix_unitaire,
                'prix_estime': prix_estime,
                'image': item.ingredient.image,
                'categorie': item.ingredient.categorie,
                'achete': False,
                'quantite_achetee': item.quantite,
                'quantite_restante': item.quantite
            })
        
        return jsonify({
            'success': True,
            'items': courses_list,
            'count': len(courses_list),
            'total_estime': round(total_estime, 2)
        })
    
    except Exception as e:
        current_app.logger.error(f'Erreur dans get_courses: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/courses/historique', methods=['GET'])
@require_api_key
def get_historique():
    """
    Récupérer l'historique des achats
    ✅ OPTIMISÉ : Utilise joinedload
    """
    try:
        # ✅ Charge les ingrédients en une seule requête
        items = ListeCourses.query.options(
            joinedload(ListeCourses.ingredient)
        ).filter_by(achete=True)\
         .order_by(ListeCourses.id.desc())\
         .limit(50)\
         .all()
        
        historique_list = []
        
        for item in items:
            prix_total = item.quantite * (item.ingredient.prix_unitaire or 0)
            
            historique_list.append({
                'id': item.id,
                'ingredient_id': item.ingredient_id,
                'ingredient_nom': item.ingredient.nom,
                'quantite': item.quantite,
                'unite': item.ingredient.unite,
                'prix_unitaire': item.ingredient.prix_unitaire,
                'prix_total': round(prix_total, 2),
                'image': item.ingredient.image,
                'categorie': item.ingredient.categorie
            })
        
        return jsonify({
            'success': True,
            'items': historique_list,
            'count': len(historique_list)
        })
    
    except Exception as e:
        current_app.logger.error(f'Erreur dans get_historique: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/courses/sync', methods=['POST'])
@require_api_key
def sync_courses():
    """
    Synchroniser les achats effectués depuis l'app Android
    Marque les items comme achetés et met à jour le frigo
    """
    try:
        data = request.get_json()
        
        if not data or 'achats' not in data:
            return jsonify({
                'success': False,
                'error': 'Format de données invalide'
            }), 400
        
        achats = data['achats']
        items_modifies = 0
        
        for achat in achats:
            item_id = achat.get('id')
            quantite_achetee = float(achat.get('quantite_achetee', 0))
            
            if not item_id or quantite_achetee <= 0:
                continue
            
            # Récupérer l'item de la liste de courses
            item = ListeCourses.query.get(item_id)
            if not item:
                continue
            
            # Mettre à jour le stock du frigo
            stock = StockFrigo.query.filter_by(ingredient_id=item.ingredient_id).first()
            if stock:
                stock.quantite += quantite_achetee
            else:
                stock = StockFrigo(
                    ingredient_id=item.ingredient_id,
                    quantite=quantite_achetee
                )
                db.session.add(stock)
            
            # Marquer l'item comme acheté
            item.achete = True
            items_modifies += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'{items_modifies} article(s) synchronisé(s) et ajouté(s) au frigo',
            'items_modifies': items_modifies
        })
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Erreur dans sync_courses: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/courses/<int:item_id>', methods=['DELETE'])
@require_api_key
def delete_course_item(item_id):
    """Supprimer un item de la liste de courses"""
    try:
        item = ListeCourses.query.get_or_404(item_id)
        nom = item.ingredient.nom
        
        db.session.delete(item)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'{nom} retiré de la liste'
        })
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Erreur dans delete_course_item: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/stock', methods=['GET'])
@require_api_key
def get_stock():
    """
    Récupérer l'état du stock (utile pour info dans l'app)
    ✅ OPTIMISÉ : Utilise joinedload
    """
    try:
        # ✅ Charge les ingrédients en une seule requête
        stocks = StockFrigo.query.options(
            joinedload(StockFrigo.ingredient)
        ).all()
        
        # Sérialisation avec to_dict()
        stock_list = [stock.to_dict() for stock in stocks]
        
        return jsonify({
            'success': True,
            'items': stock_list,
            'count': len(stock_list)
        })
    
    except Exception as e:
        current_app.logger.error(f'Erreur dans get_stock: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/ingredients', methods=['GET'])
@require_api_key
def get_ingredients():
    """
    Récupérer la liste des ingrédients (pour recherche/ajout manuel)
    ✅ OPTIMISÉ : Utilise joinedload pour charger le stock
    """
    try:
        # ✅ Charge le stock en même temps si nécessaire
        ingredients = Ingredient.query.options(
            joinedload(Ingredient.stock)
        ).order_by(Ingredient.nom).all()
        
        # Sérialisation avec to_dict()
        ingredients_list = [ing.to_dict(include_stock=True) for ing in ingredients]
        
        return jsonify({
            'success': True,
            'items': ingredients_list,
            'count': len(ingredients_list)
        })
    
    except Exception as e:
        current_app.logger.error(f'Erreur dans get_ingredients: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 500
