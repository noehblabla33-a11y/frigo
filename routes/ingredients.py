"""
routes/ingredients.py (VERSION REFACTORISÉE)
Gestion du catalogue d'ingrédients

CHANGEMENTS:
- Utilise utils/validators.py pour les validations
- Utilise utils/queries.py pour le comptage des catégories
- Utilise systématiquement utils/files.py pour les images
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from models.models import db, Ingredient
from utils.pagination import paginate_query
from utils.files import save_uploaded_file, delete_file
from utils.database import db_transaction_with_flash
from utils.forms import (
    parse_float, parse_float_or_none, clean_string, 
    clean_string_or_none, parse_nutrition_values
)
from constants import CATEGORIES
# ✅ NOUVEAUX IMPORTS
from utils.validators import validate_unique_ingredient, validate_categorie
from utils.queries import get_categories_count

ingredients_bp = Blueprint('ingredients', __name__)

# Constante pour la pagination (fallback)
ITEMS_PER_PAGE = 24


@ingredients_bp.route('/', methods=['GET', 'POST'])
def liste():
    if request.method == 'POST':
        nom = clean_string(request.form.get('nom'))
        unite = clean_string(request.form.get('unite'), 'g')
        prix_unitaire = parse_float(request.form.get('prix_unitaire'))
        categorie = clean_string_or_none(request.form.get('categorie'))
        poids_piece = parse_float_or_none(request.form.get('poids_piece'))

        # ✅ REFACTORISÉ: Validations centralisées
        if not validate_unique_ingredient(nom):
            return redirect(url_for('ingredients.liste'))
        
        if not validate_categorie(categorie, CATEGORIES):
            return redirect(url_for('ingredients.liste'))

        # Valeurs nutritionnelles
        nutrition = parse_nutrition_values(request.form)

        try:
            with db_transaction_with_flash(
                success_message=f'Ingrédient "{nom}" ajouté au catalogue !',
                error_message='Erreur lors de l\'ajout de l\'ingrédient'
            ):
                ingredient = Ingredient(
                    nom=nom,
                    unite=unite,
                    prix_unitaire=prix_unitaire,
                    categorie=categorie,
                    poids_piece=poids_piece,
                    **nutrition
                )
                
                # ✅ REFACTORISÉ: Utilisation de save_uploaded_file
                if 'image' in request.files:
                    filepath = save_uploaded_file(
                        request.files['image'], 
                        prefix=f'ing_{nom}'
                    )
                    if filepath:
                        ingredient.image = filepath
                
                db.session.add(ingredient)
        
        except Exception as e:
            current_app.logger.error(f'Erreur ajout ingrédient: {str(e)}')
            
        return redirect(url_for('ingredients.liste'))
    
    # ============================================
    # GET - AFFICHAGE DE LA LISTE
    # ============================================
    
    search_query = request.args.get('search', '')
    categorie_filter = request.args.get('categorie', '')
    stock_filter = request.args.get('stock', '')
    page = request.args.get('page', 1, type=int)

    items_per_page = current_app.config.get('ITEMS_PER_PAGE_DEFAULT', ITEMS_PER_PAGE)
    
    # Construire la requête
    query = Ingredient.query
    
    if search_query:
        query = query.filter(Ingredient.nom.ilike(f'%{search_query}%'))
    
    if categorie_filter:
        query = query.filter(Ingredient.categorie == categorie_filter)
    
    query = query.order_by(Ingredient.nom)
    
    # Gestion du filtre par stock
    if stock_filter:
        all_ingredients = query.all()
        
        if stock_filter == 'en_stock':
            filtered = [ing for ing in all_ingredients if ing.stock and ing.stock.quantite > 0]
        elif stock_filter == 'pas_en_stock':
            filtered = [ing for ing in all_ingredients if not ing.stock or ing.stock.quantite == 0]
        else:
            filtered = all_ingredients
        
        # Pagination manuelle
        total = len(filtered)
        pages = (total + items_per_page - 1) // items_per_page if total > 0 else 1
        page = min(max(1, page), pages)
        start = (page - 1) * items_per_page
        end = start + items_per_page
        
        pagination = {
            'items': filtered[start:end],
            'total': total,
            'page': page,
            'pages': pages,
            'per_page': items_per_page,
            'has_prev': page > 1,
            'has_next': page < pages,
            'prev_page': page - 1 if page > 1 else None,
            'next_page': page + 1 if page < pages else None
        }
    else:
        pagination = paginate_query(query, page, items_per_page)
    
    # ✅ REFACTORISÉ: Comptage en une seule requête
    categories_count = get_categories_count()
    
    return render_template(
        'ingredients.html', 
        ingredients=pagination['items'],
        pagination=pagination,
        categories=CATEGORIES,
        categories_count=categories_count,
        search_query=search_query,
        categorie_filter=categorie_filter,
        stock_filter=stock_filter
    )


@ingredients_bp.route('/modifier/<int:id>', methods=['GET', 'POST'])
def modifier(id):
    ingredient = Ingredient.query.get_or_404(id)
    
    if request.method == 'POST':
        nouveau_nom = clean_string(request.form.get('nom'))
        categorie = clean_string_or_none(request.form.get('categorie'))
        
        # ✅ REFACTORISÉ: Validation centralisée (avec exclusion de l'ID actuel)
        if nouveau_nom != ingredient.nom:
            if not validate_unique_ingredient(nouveau_nom, exclude_id=id):
                return redirect(url_for('ingredients.modifier', id=id))
        
        if not validate_categorie(categorie, CATEGORIES):
            return redirect(url_for('ingredients.modifier', id=id))
        
        try:
            with db_transaction_with_flash(
                success_message=f'Ingrédient "{nouveau_nom}" modifié !',
                error_message='Erreur lors de la modification'
            ):
                ingredient.nom = nouveau_nom
                ingredient.unite = clean_string(request.form.get('unite'), 'g')
                ingredient.prix_unitaire = parse_float(request.form.get('prix_unitaire'))
                ingredient.categorie = categorie
                ingredient.poids_piece = parse_float_or_none(request.form.get('poids_piece'))

                # Valeurs nutritionnelles
                nutrition = parse_nutrition_values(request.form)
                for key, value in nutrition.items():
                    setattr(ingredient, key, value)
                
                # ✅ REFACTORISÉ: Gestion image avec utils/files.py
                if 'image' in request.files:
                    file = request.files['image']
                    if file and file.filename:
                        # Supprimer l'ancienne
                        if ingredient.image:
                            delete_file(ingredient.image)
                        
                        # Sauvegarder la nouvelle
                        filepath = save_uploaded_file(file, prefix=f'ing_{ingredient.nom}')
                        if filepath:
                            ingredient.image = filepath
        
        except Exception as e:
            current_app.logger.error(f'Erreur modification ingrédient: {str(e)}')
            
        return redirect(url_for('ingredients.liste'))
    
    return render_template(
        'ingredient_modifier.html', 
        ingredient=ingredient, 
        categories=CATEGORIES
    )


@ingredients_bp.route('/supprimer/<int:id>')
def supprimer(id):
    from utils.validators import validate_ingredient_not_used
    
    ingredient = Ingredient.query.get_or_404(id)
    nom = ingredient.nom
    
    # ✅ REFACTORISÉ: Validation centralisée
    peut_supprimer, recettes = validate_ingredient_not_used(ingredient)
    
    if not peut_supprimer:
        return redirect(url_for('ingredients.liste'))
    
    try:
        with db_transaction_with_flash(
            success_message=f'Ingrédient "{nom}" supprimé du catalogue !',
            error_message='Erreur lors de la suppression'
        ):
            # Supprimer l'image associée
            if ingredient.image:
                delete_file(ingredient.image)
            
            db.session.delete(ingredient)
    
    except Exception as e:
        current_app.logger.error(f'Erreur suppression ingrédient: {str(e)}')
        flash(f'Erreur lors de la suppression : {str(e)}', 'danger')
        
    return redirect(url_for('ingredients.liste'))


@ingredients_bp.route('/supprimer-image/<int:id>')
def supprimer_image(id):
    """
    Supprime uniquement l'image d'un ingrédient
    """
    ingredient = Ingredient.query.get_or_404(id)
    
    if ingredient.image:
        try:
            with db_transaction_with_flash(
                success_message=f'Image de "{ingredient.nom}" supprimée.',
                error_message='Erreur lors de la suppression de l\'image'
            ):
                delete_file(ingredient.image)
                ingredient.image = None
        except Exception as e:
            current_app.logger.error(f'Erreur suppression image: {str(e)}')
    else:
        flash('Cet ingrédient n\'a pas d\'image.', 'info')
    
    return redirect(url_for('ingredients.modifier', id=id))
