"""
routes/api.py
API REST pour l'application Android
"""
from flask import Blueprint, jsonify, request
from models.models import db, ListeCourses, StockFrigo, Ingredient
from functools import wraps
import hashlib
import secrets

api_bp = Blueprint('api', __name__)

# Clé API simple (à remplacer par un système plus robuste en production)
API_KEY = "ma_clef"

def require_api_key(f):
    """Décorateur pour vérifier la clé API"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key or api_key != API_KEY:
            return jsonify({'error': 'Clé API invalide'}), 401
        return f(*args, **kwargs)
    return decorated_function


@api_bp.route('/health', methods=['GET'])
def health():
    """Vérifier que l'API est accessible"""
    return jsonify({'status': 'ok', 'message': 'API opérationnelle'})


@api_bp.route('/courses', methods=['GET'])
@require_api_key
def get_courses():
    """
    Récupérer la liste de courses non achetée
    
    Returns:
        JSON avec la liste des items à acheter
    """
    items = ListeCourses.query.filter_by(achete=False).all()
    
    courses_list = []
    for item in items:
        courses_list.append({
            'id': item.id,
            'ingredient_id': item.ingredient_id,
            'ingredient_nom': item.ingredient.nom,
            'quantite': item.quantite,
            'unite': item.ingredient.unite,
            'prix_unitaire': item.ingredient.prix_unitaire,
            'prix_estime': item.quantite * item.ingredient.prix_unitaire if item.ingredient.prix_unitaire else 0,
            'image': item.ingredient.image,
            'categorie': item.ingredient.categorie
        })
    
    # Calculer le total estimé
    total_estime = sum(item['prix_estime'] for item in courses_list if item['prix_estime'] > 0)
    
    return jsonify({
        'success': True,
        'items': courses_list,
        'count': len(courses_list),
        'total_estime': round(total_estime, 2)
    })


@api_bp.route('/courses/sync', methods=['POST'])
@require_api_key
def sync_courses():
    """
    Synchroniser les achats depuis l'application Android
    
    Payload attendu:
    {
        "achats": [
            {
                "id": 1,
                "quantite_achetee": 2.5,
                "achete": true
            },
            ...
        ]
    }
    
    Returns:
        JSON avec le statut de la synchronisation
    """
    try:
        data = request.get_json()
        
        if not data or 'achats' not in data:
            return jsonify({'success': False, 'error': 'Données invalides'}), 400
        
        achats = data['achats']
        items_modifies = 0
        
        for achat in achats:
            item_id = achat.get('id')
            quantite_achetee = achat.get('quantite_achetee')
            achete = achat.get('achete', False)
            
            if not item_id:
                continue
            
            item = ListeCourses.query.get(item_id)
            if not item:
                continue
            
            # Si l'item est marqué comme acheté
            if achete:
                # Mettre à jour le stock
                stock = StockFrigo.query.filter_by(ingredient_id=item.ingredient_id).first()
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
                item.quantite = quantite_achetee
                items_modifies += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'{items_modifies} article(s) synchronisé(s)',
            'items_modifies': items_modifies
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/courses/<int:item_id>', methods=['DELETE'])
@require_api_key
def delete_course_item(item_id):
    """
    Supprimer un item de la liste de courses
    
    Args:
        item_id: ID de l'item à supprimer
    """
    item = ListeCourses.query.get(item_id)
    
    if not item:
        return jsonify({'success': False, 'error': 'Item introuvable'}), 404
    
    nom = item.ingredient.nom
    db.session.delete(item)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'{nom} retiré de la liste'
    })


@api_bp.route('/stock', methods=['GET'])
@require_api_key
def get_stock():
    """
    Récupérer l'état du stock (utile pour info dans l'app)
    """
    stocks = StockFrigo.query.all()
    
    stock_list = []
    for stock in stocks:
        stock_list.append({
            'ingredient_id': stock.ingredient_id,
            'ingredient_nom': stock.ingredient.nom,
            'quantite': stock.quantite,
            'unite': stock.ingredient.unite,
            'derniere_modif': stock.date_modification.isoformat()
        })
    
    return jsonify({
        'success': True,
        'items': stock_list,
        'count': len(stock_list)
    })


@api_bp.route('/ingredients', methods=['GET'])
@require_api_key
def get_ingredients():
    """
    Récupérer la liste des ingrédients (pour recherche/ajout manuel)
    """
    ingredients = Ingredient.query.order_by(Ingredient.nom).all()
    
    ingredients_list = []
    for ing in ingredients:
        ingredients_list.append({
            'id': ing.id,
            'nom': ing.nom,
            'unite': ing.unite,
            'prix_unitaire': ing.prix_unitaire,
            'categorie': ing.categorie,
            'image': ing.image,
            'en_stock': ing.stock is not None and ing.stock.quantite > 0,
            'quantite_stock': ing.stock.quantite if ing.stock else 0
        })
    
    return jsonify({
        'success': True,
        'items': ingredients_list,
        'count': len(ingredients_list)
    })

