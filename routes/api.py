"""
routes/api.py
API REST pour l'application Android

✅ VERSION OPTIMISÉE - PHASE 1
- Clé API chargée depuis config (pas hardcodée)
- Requêtes optimisées avec joinedload (pas de N+1)
- Gestion d'erreurs améliorée

✅ REFACTORISÉ : Utilise utils/calculs.py pour le calcul du budget
"""
from flask import Blueprint, jsonify, request, current_app
from models.models import db, ListeCourses, StockFrigo, Ingredient
from functools import wraps
from sqlalchemy.orm import joinedload
from utils.calculs import calculer_budget_courses, calculer_prix_item  # ✅ NOUVEAU
from utils.stock import ajouter_au_stock 

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
    ✅ REFACTORISÉ : Utilise calculer_budget_courses pour le total
    """
    try:
        # ✅ Charge les ingrédients en une seule requête
        items = ListeCourses.query.options(
            joinedload(ListeCourses.ingredient)
        ).filter_by(achete=False).all()
        
        # ✅ REFACTORISÉ : Utilisation de la fonction centralisée avec détails
        budget = calculer_budget_courses(items, include_details=True)
        
        # Enrichir les détails avec les infos supplémentaires pour l'API
        courses_list = []
        for item, detail in zip(items, budget.details):
            courses_list.append({
                **detail,
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
            'total_estime': budget.total_estime
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
    ✅ REFACTORISÉ : Utilise calculer_prix_item
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
            # ✅ REFACTORISÉ : Utilisation de la fonction centralisée
            prix_total = calculer_prix_item(item)
            
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
    
    ✅ VERSION REFACTORISÉE - Utilise utils/stock.py
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
            item = ListeCourses.query.options(
                joinedload(ListeCourses.ingredient)
            ).get(item_id)
            
            if not item or item.achete:
                continue
            
            # ✅ REFACTORISÉ: Une seule ligne au lieu de 10 !
            ajouter_au_stock(item.ingredient_id, quantite_achetee)
            
            # Marquer comme acheté
            item.achete = True
            items_modifies += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'items_modifies': items_modifies,
            'message': f'{items_modifies} article(s) synchronisé(s)'
        })
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Erreur dans sync_courses: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/frigo', methods=['GET'])
@require_api_key
def get_frigo():
    """
    Récupérer le contenu du frigo
    ✅ OPTIMISÉ : Utilise joinedload
    """
    try:
        stocks = StockFrigo.query.options(
            joinedload(StockFrigo.ingredient)
        ).filter(StockFrigo.quantite > 0).all()
        
        frigo_list = []
        
        for stock in stocks:
            frigo_list.append({
                'id': stock.id,
                'ingredient_id': stock.ingredient_id,
                'ingredient_nom': stock.ingredient.nom,
                'quantite': stock.quantite,
                'unite': stock.ingredient.unite,
                'prix_unitaire': stock.ingredient.prix_unitaire,
                'image': stock.ingredient.image,
                'categorie': stock.ingredient.categorie,
                'date_modification': stock.date_modification.isoformat() if stock.date_modification else None
            })
        
        return jsonify({
            'success': True,
            'items': frigo_list,
            'count': len(frigo_list)
        })
    
    except Exception as e:
        current_app.logger.error(f'Erreur dans get_frigo: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/ingredients', methods=['GET'])
@require_api_key
def get_ingredients():
    """
    Récupérer le catalogue des ingrédients
    """
    try:
        ingredients = Ingredient.query.order_by(Ingredient.nom).all()
        
        ingredients_list = []
        
        for ing in ingredients:
            ingredients_list.append({
                'id': ing.id,
                'nom': ing.nom,
                'unite': ing.unite,
                'prix_unitaire': ing.prix_unitaire,
                'categorie': ing.categorie,
                'image': ing.image
            })
        
        return jsonify({
            'success': True,
            'items': ingredients_list,
            'count': len(ingredients_list)
        })
    
    except Exception as e:
        current_app.logger.error(f'Erreur dans get_ingredients: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 500
