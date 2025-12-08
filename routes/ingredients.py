from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from models.models import db, Ingredient
from werkzeug.utils import secure_filename
from utils.pagination import paginate_query
import os

ingredients_bp = Blueprint('ingredients', __name__)

# Catégories d'ingrédients
CATEGORIES = [
    ('Légumes', '🥬'),
    ('Fruits', '🍎'),
    ('Viandes', '🥩'),
    ('Poissons', '🐟'),
    ('Produits laitiers', '🥛'),
    ('Féculents', '🍚'),
    ('Épices et herbes', '🌿'),
    ('Condiments', '🧂'),
    ('Boissons', '🥤'),
    ('Boulangerie', '🥖'),
    ('Autres', '📦')
]

# Nombre d'éléments par page
ITEMS_PER_PAGE = 24

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@ingredients_bp.route('/', methods=['GET', 'POST'])
def liste():
    if request.method == 'POST':
        nom = request.form.get('nom')
        unite = request.form.get('unite', 'g')
        prix_unitaire = float(request.form.get('prix_unitaire') or 0)
        categorie = request.form.get('categorie')
        calories = float(request.form.get('calories') or 0)
        proteines = float(request.form.get('proteines') or 0)
        glucides = float(request.form.get('glucides') or 0)
        lipides = float(request.form.get('lipides') or 0)
        fibres = float(request.form.get('fibres') or 0)
        sucres = float(request.form.get('sucres') or 0)
        sel = float(request.form.get('sel') or 0)
        poids_piece_str = request.form.get('poids_piece')
        poids_piece = float(poids_piece_str) if poids_piece_str else None

        
        ingredient = Ingredient.query.filter_by(nom=nom).first()
        if ingredient:
            flash(f'L\'ingrédient "{nom}" existe déjà !', 'danger')
            return redirect(url_for('ingredients.liste'))
        
        ingredient = Ingredient(
            nom=nom, 
            unite=unite, 
            prix_unitaire=prix_unitaire,
            categorie=categorie if categorie else None,
            calories=calories,
            proteines=proteines,
            glucides=glucides,
            lipides=lipides,
            fibres=fibres,
            sucres=sucres,
            sel=sel,
            poids_piece=poids_piece
        )
        
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(f"ing_{nom}_{file.filename}")
                filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                file.save(os.path.join(current_app.root_path, filepath))
                ingredient.image = filepath
        
        db.session.add(ingredient)
        db.session.commit()
        flash(f'Ingrédient "{nom}" ajouté au catalogue !', 'success')
        return redirect(url_for('ingredients.liste'))
    
    # Gestion de la recherche et des filtres
    search_query = request.args.get('search', '')
    categorie_filter = request.args.get('categorie', '')
    stock_filter = request.args.get('stock', '')
    view_mode = request.args.get('view', 'grid')
    page = request.args.get('page', 1, type=int)
    
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
        pagination = paginate_query(query, page, ITEMS_PER_PAGE)
    
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
                         stock_filter=stock_filter,
                         view_mode=view_mode)

@ingredients_bp.route('/modifier/<int:id>', methods=['GET', 'POST'])
def modifier(id):
    ingredient = Ingredient.query.get_or_404(id)
    
    if request.method == 'POST':
        ingredient.nom = request.form.get('nom')
        ingredient.unite = request.form.get('unite')
        ingredient.prix_unitaire = float(request.form.get('prix_unitaire') or 0)
        ingredient.categorie = request.form.get('categorie')

        # ✅ AJOUT : Récupération des valeurs nutritionnelles
        ingredient.calories = float(request.form.get('calories') or 0)
        ingredient.proteines = float(request.form.get('proteines') or 0)
        ingredient.glucides = float(request.form.get('glucides') or 0)
        ingredient.lipides = float(request.form.get('lipides') or 0)
        ingredient.fibres = float(request.form.get('fibres') or 0)
        ingredient.sucres = float(request.form.get('sucres') or 0)
        ingredient.sel = float(request.form.get('sel') or 0)

        poids_piece_str = request.form.get('poids_piece')
        ingredient.poids_piece = float(poids_piece_str) if poids_piece_str else None
        
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename != '' and allowed_file(file.filename):
                if ingredient.image:
                    try:
                        os.remove(os.path.join(current_app.root_path, ingredient.image))
                    except:
                        pass
                
                filename = secure_filename(f"ing_{ingredient.nom}_{file.filename}")
                filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                file.save(os.path.join(current_app.root_path, filepath))
                ingredient.image = filepath
        
        db.session.commit()
        flash(f'Ingrédient "{ingredient.nom}" modifié !', 'success')
        return redirect(url_for('ingredients.liste'))
    
    return render_template('ingredient_modifier.html', ingredient=ingredient, categories=CATEGORIES)

@ingredients_bp.route('/supprimer/<int:id>')
def supprimer(id):
    ingredient = Ingredient.query.get_or_404(id)
    nom = ingredient.nom
    
    if ingredient.recettes:
        flash(f'Impossible de supprimer "{nom}" car il est utilisé dans des recettes !', 'danger')
        return redirect(url_for('ingredients.liste'))
    
    if ingredient.image:
        try:
            os.remove(os.path.join(current_app.root_path, ingredient.image))
        except:
            pass
    
    db.session.delete(ingredient)
    db.session.commit()
    flash(f'Ingrédient "{nom}" supprimé du catalogue !', 'success')
    return redirect(url_for('ingredients.liste'))
