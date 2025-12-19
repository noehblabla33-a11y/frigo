from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from models.models import db, Ingredient
from werkzeug.utils import secure_filename
from utils.pagination import paginate_query
from utils.files import allowed_file, save_uploaded_file, delete_file
from utils.database import db_transaction_with_flash, db_delete_with_check
from utils.forms import parse_float, parse_float_or_none, clean_string, clean_string_or_none, parse_nutrition_values
from constants import CATEGORIES, valider_categorie
import os

ingredients_bp = Blueprint('ingredients', __name__)

@ingredients_bp.route('/', methods=['GET', 'POST'])
def liste():
    if request.method == 'POST':
        nom = clean_string(request.form.get('nom'))
        unite = clean_string(request.form.get('unite'), 'g')
        prix_unitaire = parse_float(request.form.get('prix_unitaire'))
        categorie = clean_string_or_none(request.form.get('categorie'))

        # Vérification de catégorie
        if categorie and not valider_categorie(categorie):
            flash(f'Catégorie invalide : {categorie}', 'danger')
            return redirect(url_for('ingredients.liste'))

        # Valeurs nutritionnelles (une seule ligne !)
        nutrition = parse_nutrition_values(request.form)

        poids_piece = parse_float_or_none(request.form.get('poids_piece'))

        ingredient = Ingredient.query.filter_by(nom=nom).first()
        if ingredient:
            flash(f'L\'ingrédient "{nom}" existe déjà !', 'danger')
            return redirect(url_for('ingredients.liste'))
        
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
                
                # Gérer l'upload de l'image
                if 'image' in request.files:
                    file = request.files['image']
                    if file and file.filename != '' and allowed_file(file.filename):
                        filename = secure_filename(f"ing_{nom}_{file.filename}")
                        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                        file.save(os.path.join(current_app.root_path, filepath))
                        ingredient.image = f'uploads/{filename}'
                
                db.session.add(ingredient)
                # ✅ Le commit et le flash sont gérés automatiquement par le context manager
        
        except Exception:
            # ✅ Le rollback et le flash d'erreur sont automatiques
            pass
            
        return redirect(url_for('ingredients.liste'))
    
    # Gestion de la recherche et des filtres
    search_query = request.args.get('search', '')
    categorie_filter = request.args.get('categorie', '')
    stock_filter = request.args.get('stock', '')
    page = request.args.get('page', 1, type=int)

    items_per_page = current_app.config.get('ITEMS_PER_PAGE_DEFAULT', 24)
    
    # Construire la requête
    query = Ingredient.query
    
    # Filtre par recherche
    if search_query:
        query = query.filter(Ingredient.nom.ilike(f'%{search_query}%'))
    
    # Filtre par catégorie
    if categorie_filter:
        query = query.filter(Ingredient.categorie == categorie_filter)
    
    # Récupérer avec pagination
    query = query.order_by(Ingredient.nom)
    
    # Si filtre par stock, on doit récupérer tous puis filtrer (relation complexe)
    if stock_filter:
        # Récupérer tous les ingrédients filtrés
        all_ingredients = query.all()
        
        # Filtrer par stock
        if stock_filter == 'en_stock':
            filtered = [ing for ing in all_ingredients if ing.stock and ing.stock.quantite > 0]
        elif stock_filter == 'pas_en_stock':
            filtered = [ing for ing in all_ingredients if not ing.stock or ing.stock.quantite == 0]
        else:
            filtered = all_ingredients
        
        # Paginer manuellement
        total = len(filtered)
        pages = (total + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE if total > 0 else 1
        page = min(max(1, page), pages)
        start = (page - 1) * ITEMS_PER_PAGE
        end = start + ITEMS_PER_PAGE
        
        pagination = {
            'items': filtered[start:end],
            'total': total,
            'page': page,
            'pages': pages,
            'per_page': ITEMS_PER_PAGE,
            'has_prev': page > 1,
            'has_next': page < pages,
            'prev_page': page - 1 if page > 1 else None,
            'next_page': page + 1 if page < pages else None
        }
    else:
        # Pagination normale
        pagination = paginate_query(query, page, items_per_page)
    
    # Compter les ingrédients par catégorie
    categories_count = {}
    for cat_name, cat_icon in CATEGORIES:
        count = Ingredient.query.filter_by(categorie=cat_name).count()
        if count > 0:
            categories_count[cat_name] = count
    
    return render_template('ingredients.html', 
                         ingredients=pagination['items'],
                         pagination=pagination,
                         categories=CATEGORIES,
                         categories_count=categories_count,
                         search_query=search_query,
                         categorie_filter=categorie_filter,
                         stock_filter=stock_filter)

@ingredients_bp.route('/modifier/<int:id>', methods=['GET', 'POST'])
def modifier(id):
    ingredient = Ingredient.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            with db_transaction_with_flash(success_message=f'Ingrédient "{ingredient.nom}" modifié !', error_message='Erreur lors de la modification'):
                ingredient.nom = clean_string(request.form.get('nom'))
                ingredient.unite = clean_string(request.form.get('unite'), 'g')
                ingredient.prix_unitaire = parse_float(request.form.get('prix_unitaire'))
                ingredient.categorie = clean_string_or_none(request.form.get('categorie'))

                # Valeurs nutritionnelles
                nutrition = parse_nutrition_values(request.form)
                for key, value in nutrition.items():
                    setattr(ingredient, key, value)

                ingredient.poids_piece = parse_float_or_none(request.form.get('poids_piece'))
                
                # Gérer l'upload de la nouvelle image
                if 'image' in request.files:
                    file = request.files['image']
                    if file and file.filename != '' and allowed_file(file.filename):
                        # Supprimer l'ancienne image
                        if ingredient.image:
                            try:
                                os.remove(os.path.join(current_app.root_path, ingredient.image))
                            except:
                                pass
                        
                        # Sauvegarder la nouvelle image
                        filename = secure_filename(f"ing_{ingredient.nom}_{file.filename}")
                        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                        file.save(os.path.join(current_app.root_path, filepath))
                        ingredient.image = filepath
                
                # ✅ Le commit est automatique
        
        except Exception:
            # ✅ Le rollback est automatique
            pass
            
        return redirect(url_for('ingredients.liste'))
    
    return render_template('ingredient_modifier.html', ingredient=ingredient, categories=CATEGORIES)

@ingredients_bp.route('/supprimer/<int:id>')
def supprimer(id):
    ingredient = Ingredient.query.get_or_404(id)
    nom = ingredient.nom
    
    try:
        with db_delete_with_check(
            ingredient,
            check_relationships=['recettes'],  # Vérifier qu'il n'est pas utilisé dans des recettes
            success_message=f'Ingrédient "{nom}" supprimé du catalogue !'
        ):
            if ingredient.image:
                try:
                    os.remove(os.path.join(current_app.root_path, ingredient.image))
                except:
                    pass
            
            # ✅ La suppression et le commit sont automatiques
    
    except ValueError as e:
        # Erreur de vérification (ingrédient utilisé dans des recettes)
        flash(str(e), 'danger')
    
    except Exception as e:
        # Autre erreur
        flash(f'Erreur lors de la suppression : {str(e)}', 'danger')
        
    return redirect(url_for('ingredients.liste'))
