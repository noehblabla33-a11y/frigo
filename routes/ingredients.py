from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from models.models import db, Ingredient
from werkzeug.utils import secure_filename
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
        
        ingredient = Ingredient.query.filter_by(nom=nom).first()
        if ingredient:
            flash(f'L\'ingrédient "{nom}" existe déjà !', 'danger')
            return redirect(url_for('ingredients.liste'))
        
        ingredient = Ingredient(
            nom=nom, 
            unite=unite, 
            prix_unitaire=prix_unitaire,
            categorie=categorie if categorie else None
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
    stock_filter = request.args.get('stock', '')  # 'en_stock', 'pas_en_stock', ou ''
    
    # Construire la requête
    query = Ingredient.query
    
    # Filtre par recherche
    if search_query:
        query = query.filter(Ingredient.nom.ilike(f'%{search_query}%'))
    
    # Filtre par catégorie
    if categorie_filter:
        query = query.filter(Ingredient.categorie == categorie_filter)
    
    # Récupérer tous les ingrédients
    all_ingredients = query.order_by(Ingredient.nom).all()
    
    # Filtre par stock (en Python car relation complexe)
    if stock_filter == 'en_stock':
        ingredients = [ing for ing in all_ingredients if ing.stock and ing.stock.quantite > 0]
    elif stock_filter == 'pas_en_stock':
        ingredients = [ing for ing in all_ingredients if not ing.stock or ing.stock.quantite == 0]
    else:
        ingredients = all_ingredients
    
    # Compter les ingrédients par catégorie
    categories_count = {}
    for cat_name, cat_icon in CATEGORIES:
        count = Ingredient.query.filter_by(categorie=cat_name).count()
        if count > 0:
            categories_count[cat_name] = count
    
    return render_template('ingredients.html', 
                         ingredients=ingredients,
                         categories=CATEGORIES,
                         categories_count=categories_count,
                         search_query=search_query,
                         categorie_filter=categorie_filter,
                         stock_filter=stock_filter)

@ingredients_bp.route('/modifier/<int:id>', methods=['GET', 'POST'])
def modifier(id):
    ingredient = Ingredient.query.get_or_404(id)
    
    if request.method == 'POST':
        ingredient.nom = request.form.get('nom')
        ingredient.unite = request.form.get('unite')
        ingredient.prix_unitaire = float(request.form.get('prix_unitaire') or 0)
        ingredient.categorie = request.form.get('categorie')
        
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

