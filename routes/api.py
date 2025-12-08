"""
routes/api.py
API REST pour l'application Android
"""
from flask import Blueprint, jsonify, request
from models.models import db, ListeCourses, StockFrigo, Ingredient
from functools import wraps
from sqlalchemy.orm import joinedload
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
    try:
        """items = ListeCourses.query.filter_by(achete=False).all()"""
        items = ListeCourses.query.options(joinedload(ListeCourses.ingredient)).filter_by(achete=False).all()
        
        courses_list = []
        total_estime = 0
        
        for item in items:
            prix_estime = item.quantite * item.ingredient.prix_unitaire if item.ingredient.prix_unitaire else 0
            total_estime += prix_estime
            
            courses_list.append({
                'id': item.id,
                'ingredient_id': item.ingredient_id,
                'ingredient_nom': item.ingredient.nom,
                'quantite': item.quantite,  # Quantité initialement demandée
                'unite': item.ingredient.unite,
                'prix_unitaire': item.ingredient.prix_unitaire,
                'prix_estime': prix_estime,
                'image': item.ingredient.image,
                'categorie': item.ingredient.categorie,
                'achete': False,
                'quantite_achetee': item.quantite,  # Par défaut = quantité demandée
                'quantite_restante': item.quantite  # Quantité encore à acheter
            })
        
        return jsonify({
            'success': True,
            'items': courses_list,
            'count': len(courses_list),
            'total_estime': total_estime
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/courses/historique', methods=['GET'])
@require_api_key
def get_historique():
    try:
        # Récupérer les 50 derniers achats
        items = ListeCourses.query.filter_by(achete=True)\
            .order_by(ListeCourses.id.desc())\
            .limit(50)\
            .all()
        
        historique_list = []
        
        for item in items:
            prix_total = item.quantite * item.ingredient.prix_unitaire if item.ingredient.prix_unitaire else 0
            
            historique_list.append({
                'id': item.id,
                'ingredient_id': item.ingredient_id,
                'ingredient_nom': item.ingredient.nom,
                'quantite': item.quantite,
                'unite': item.ingredient.unite,
                'prix_unitaire': item.ingredient.prix_unitaire,
                'prix_total': prix_total,
                'image': item.ingredient.image,
                'categorie': item.ingredient.categorie
            })
        
        return jsonify({
            'success': True,
            'items': historique_list,
            'count': len(historique_list)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/courses/sync', methods=['POST'])
@require_api_key
def sync_courses():
    try:
        data = request.get_json()
        achats = data.get('achats', [])
        
        items_modifies = 0
        
        for achat in achats:
            item_id = achat.get('id')
            quantite_achetee = achat.get('quantite_achetee', 0)
            achete = achat.get('achete', False)
            
            # Trouver l'item dans la liste de courses
            item = ListeCourses.query.get(item_id)
            if not item or item.achete:  # Si déjà acheté, ignorer
                continue
            
            if achete and quantite_achetee > 0:
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
                
                # ⚠️ IMPORTANT : Créer une copie dans l'historique AVANT de modifier/supprimer
                item_historique = ListeCourses(
                    ingredient_id=item.ingredient_id,
                    quantite=quantite_achetee,
                    achete=True
                )
                db.session.add(item_historique)
                
                # Réduire la quantité dans la liste de courses OU supprimer
                if quantite_achetee >= item.quantite:
                    # Tout a été acheté, supprimer l'item de la liste active
                    db.session.delete(item)
                else:
                    # Partiellement acheté, réduire la quantité
                    item.quantite -= quantite_achetee
                
                items_modifies += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'{items_modifies} article(s) synchronisé(s) et ajouté(s) au frigo',
            'items_modifies': items_modifies
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500



@api_bp.route('/courses/<int:item_id>', methods=['DELETE'])
@require_api_key
def delete_course_item(item_id):
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
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/stock', methods=['GET'])
@require_api_key
def get_stock():
    """
    Récupérer l'état du stock (utile pour info dans l'app)
    """
    stocks = StockFrigo.query.all()
    
    # Sérialisation avec to_dict()
    stock_list = [stock.to_dict() for stock in stocks]
    
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
    
    # Sérialisation avec to_dict()
    ingredients_list = [ing.to_dict(include_stock=True) for ing in ingredients]
    
    return jsonify({
        'success': True,
        'items': ingredients_list,
        'count': len(ingredients_list)
    })
