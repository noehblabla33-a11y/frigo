"""
routes/ingredients.py (VERSION AVEC SAISONS)
Gestion du catalogue d'ingrédients

CHANGEMENTS:
- Utilise utils/validators.py pour les validations
- Utilise utils/queries.py pour le comptage des catégories
- Utilise systématiquement utils/files.py pour les images
- ✅ NOUVEAU: Gestion des saisons
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from models.models import db, Ingredient, IngredientSaison
from utils.pagination import paginate_query
from utils.files import save_uploaded_file, delete_file
from utils.database import db_transaction_with_flash
from utils.forms import (
    parse_float, parse_float_or_none, clean_string, 
    clean_string_or_none, parse_nutrition_values
)
from utils.saisons import get_saison_actuelle, get_ingredients_de_saison
from constants import CATEGORIES, SAISONS, SAISONS_VALIDES
from utils.validators import validate_unique_ingredient, validate_categorie
from utils.queries import get_categories_count

ingredients_bp = Blueprint('ingredients', __name__)

ITEMS_PER_PAGE = 24


def parse_saisons_list(form) -> list:
    """
    Parse les saisons sélectionnées dans le formulaire.
    
    Args:
        form: Request form
    
    Returns:
        Liste des saisons sélectionnées
    """
    saisons = []
    for saison in SAISONS_VALIDES:
        if form.get(f'saison_{saison}'):
            saisons.append(saison)
    return saisons


@ingredients_bp.route('/', methods=['GET', 'POST'])
def liste():
    if request.method == 'POST':
        nom = clean_string(request.form.get('nom'))
        unite = clean_string(request.form.get('unite'), 'g')
        prix_unitaire = parse_float(request.form.get('prix_unitaire'))
        categorie = clean_string_or_none(request.form.get('categorie'))
        poids_piece = parse_float_or_none(request.form.get('poids_piece'))

        # Validations
        if not validate_unique_ingredient(nom):
            return redirect(url_for('ingredients.liste'))
        
        if not validate_categorie(categorie, CATEGORIES):
            return redirect(url_for('ingredients.liste'))

        # Valeurs nutritionnelles
        nutrition = parse_nutrition_values(request.form)

        try:
            with db_transaction_with_flash(
                success_message=f'Ingrédient "{nom}" ajouté au catalogue !',
                error_message='Erreur lors de l\'ajout de l\'ingrédient.'
            ):
                ingredient = Ingredient(
                    nom=nom,
                    unite=unite,
                    prix_unitaire=prix_unitaire,
                    categorie=categorie,
                    poids_piece=poids_piece,
                    **nutrition
                )
                
                # Gestion de l'image
                if 'image' in request.files:
                    file = request.files['image']
                    filepath = save_uploaded_file(file, prefix=f'ing_{nom}')
                    if filepath:
                        ingredient.image = filepath
                
                db.session.add(ingredient)
                db.session.flush()  # Pour obtenir l'ID
                
                # ✅ NOUVEAU: Gestion des saisons
                saisons = parse_saisons_list(request.form)
                for saison in saisons:
                    ing_saison = IngredientSaison(
                        ingredient_id=ingredient.id,
                        saison=saison
                    )
                    db.session.add(ing_saison)
                
        except Exception as e:
            current_app.logger.error(f'Erreur création ingrédient: {e}')
        
        return redirect(url_for('ingredients.liste'))
    
    # GET - Affichage de la liste
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('search', '').strip()
    categorie_filter = request.args.get('categorie', '')
    stock_filter = request.args.get('stock', '')
    saison_filter = request.args.get('saison', '')  # ✅ NOUVEAU
    
    items_per_page = current_app.config.get('ITEMS_PER_PAGE_DEFAULT', ITEMS_PER_PAGE)
    
    # Construction de la requête de base
    query = Ingredient.query
    
    # Filtres
    if search_query:
        query = query.filter(Ingredient.nom.ilike(f'%{search_query}%'))
    
    if categorie_filter:
        query = query.filter(Ingredient.categorie == categorie_filter)
    
    if stock_filter == 'en_stock':
        from models.models import StockFrigo
        query = query.join(StockFrigo).filter(StockFrigo.quantite > 0)
    elif stock_filter == 'hors_stock':
        from models.models import StockFrigo
        query = query.outerjoin(StockFrigo).filter(
            db.or_(StockFrigo.id.is_(None), StockFrigo.quantite <= 0)
        )
    
    # ✅ NOUVEAU: Filtre par saison
    if saison_filter:
        if saison_filter == 'de_saison':
            # Ingrédients de la saison actuelle
            saison_actuelle = get_saison_actuelle()
            ingredients_saison_ids = db.session.query(IngredientSaison.ingredient_id)\
                .filter(IngredientSaison.saison == saison_actuelle)\
                .subquery()
            ingredients_sans_saison = db.session.query(Ingredient.id)\
                .outerjoin(IngredientSaison)\
                .filter(IngredientSaison.id.is_(None))\
                .subquery()
            query = query.filter(
                db.or_(
                    Ingredient.id.in_(ingredients_saison_ids),
                    Ingredient.id.in_(ingredients_sans_saison)
                )
            )
        elif saison_filter == 'hors_saison':
            # Ingrédients hors saison actuelle
            saison_actuelle = get_saison_actuelle()
            ingredients_saison_ids = db.session.query(IngredientSaison.ingredient_id)\
                .filter(IngredientSaison.saison == saison_actuelle)\
                .subquery()
            ingredients_avec_saison = db.session.query(IngredientSaison.ingredient_id.distinct())\
                .subquery()
            query = query.filter(
                Ingredient.id.in_(ingredients_avec_saison),
                ~Ingredient.id.in_(ingredients_saison_ids)
            )
        elif saison_filter in SAISONS_VALIDES:
            # Filtre par saison spécifique
            ingredients_saison_ids = db.session.query(IngredientSaison.ingredient_id)\
                .filter(IngredientSaison.saison == saison_filter)\
                .subquery()
            query = query.filter(Ingredient.id.in_(ingredients_saison_ids))
    
    query = query.order_by(Ingredient.nom)
    
    # Pagination
    pagination = paginate_query(query, page, items_per_page)
    
    # Comptage des catégories
    categories_count = get_categories_count()
    
    # ✅ NOUVEAU: Contexte saison
    saison_actuelle = get_saison_actuelle()
    
    return render_template(
        'ingredients.html', 
        ingredients=pagination['items'],
        pagination=pagination,
        categories=CATEGORIES,
        categories_count=categories_count,
        search_query=search_query,
        categorie_filter=categorie_filter,
        stock_filter=stock_filter,
        saison_filter=saison_filter,
        saisons=SAISONS,
        saison_actuelle=saison_actuelle
    )


@ingredients_bp.route('/modifier/<int:id>', methods=['GET', 'POST'])
def modifier(id):
    ingredient = Ingredient.query.get_or_404(id)
    
    if request.method == 'POST':
        nouveau_nom = clean_string(request.form.get('nom'))
        categorie = clean_string_or_none(request.form.get('categorie'))
        
        # Validation
        if nouveau_nom != ingredient.nom:
            if not validate_unique_ingredient(nouveau_nom, exclude_id=id):
                return redirect(url_for('ingredients.modifier', id=id))
        
        if not validate_categorie(categorie, CATEGORIES):
            return redirect(url_for('ingredients.modifier', id=id))
        
        try:
            with db_transaction_with_flash(
                success_message=f'Ingrédient "{nouveau_nom}" modifié !',
                error_message='Erreur lors de la modification.'
            ):
                # Mise à jour des champs de base
                ingredient.nom = nouveau_nom
                ingredient.unite = clean_string(request.form.get('unite'), 'g')
                ingredient.prix_unitaire = parse_float(request.form.get('prix_unitaire'))
                ingredient.categorie = categorie
                ingredient.poids_piece = parse_float_or_none(request.form.get('poids_piece'))
                
                # Valeurs nutritionnelles
                nutrition = parse_nutrition_values(request.form)
                for key, value in nutrition.items():
                    setattr(ingredient, key, value)
                
                # Gestion de l'image
                if 'image' in request.files:
                    file = request.files['image']
                    if file and file.filename:
                        # Supprimer l'ancienne image
                        if ingredient.image:
                            delete_file(ingredient.image)
                        # Sauvegarder la nouvelle
                        filepath = save_uploaded_file(file, prefix=f'ing_{nouveau_nom}')
                        if filepath:
                            ingredient.image = filepath
                
                # ✅ NOUVEAU: Mise à jour des saisons
                saisons = parse_saisons_list(request.form)
                
                # Supprimer les anciennes saisons
                IngredientSaison.query.filter_by(ingredient_id=ingredient.id).delete()
                
                # Ajouter les nouvelles
                for saison in saisons:
                    ing_saison = IngredientSaison(
                        ingredient_id=ingredient.id,
                        saison=saison
                    )
                    db.session.add(ing_saison)
                
        except Exception as e:
            current_app.logger.error(f'Erreur modification ingrédient: {e}')
        
        return redirect(url_for('ingredients.liste'))
    
    # GET - Affichage du formulaire
    return render_template(
        'ingredient_modifier.html', 
        ingredient=ingredient,
        categories=CATEGORIES,
        saisons=SAISONS,
        saisons_ingredient=ingredient.get_saisons()
    )


@ingredients_bp.route('/supprimer/<int:id>')
def supprimer(id):
    ingredient = Ingredient.query.get_or_404(id)
    nom = ingredient.nom
    
    try:
        # Supprimer l'image si elle existe
        if ingredient.image:
            delete_file(ingredient.image)
        
        db.session.delete(ingredient)
        db.session.commit()
        flash(f'Ingrédient "{nom}" supprimé !', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de la suppression : {str(e)}', 'danger')
        current_app.logger.error(f'Erreur suppression ingrédient: {e}')
    
    return redirect(url_for('ingredients.liste'))


# ============================================
# ✅ NOUVELLE ROUTE: Ingrédients de saison
# ============================================

@ingredients_bp.route('/de-saison')
def de_saison():
    """
    Affiche les ingrédients de la saison actuelle.
    """
    saison = request.args.get('saison', get_saison_actuelle())
    categorie = request.args.get('categorie', '')
    
    # Récupérer les ingrédients de saison
    ingredients = get_ingredients_de_saison(saison=saison, categorie=categorie if categorie else None)
    
    return render_template(
        'ingredients_saison.html',
        ingredients=ingredients,
        saison=saison,
        saisons=SAISONS,
        categories=CATEGORIES,
        categorie_filter=categorie,
        saison_actuelle=get_saison_actuelle()
    )
