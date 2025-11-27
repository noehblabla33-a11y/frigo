from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify
from models.models import db, Recette, Ingredient, IngredientRecette, RecettePlanifiee, EtapeRecette
from werkzeug.utils import secure_filename
import os

recettes_bp = Blueprint('recettes', __name__)

TYPES_RECETTES = [
    'Entrée', 'Plat principal', 'Accompagnement', 'Dessert', 'Petit-déjeuner',
    'Salade', 'Soupe', 'Au four', 'À la poêle', 'À la casserole',
    'Sans cuisson', 'Boisson', 'Autre'
]

# Nombre d'éléments par page
ITEMS_PER_PAGE = 20

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def paginate_query(query, page, per_page=ITEMS_PER_PAGE):
    """Helper de pagination"""
    page = max(1, page)
    total = query.count()
    pages = (total + per_page - 1) // per_page if total > 0 else 1
    page = min(page, pages)
    items = query.limit(per_page).offset((page - 1) * per_page).all()
    
    return {
        'items': items,
        'total': total,
        'page': page,
        'pages': pages,
        'per_page': per_page,
        'has_prev': page > 1,
        'has_next': page < pages,
        'prev_page': page - 1 if page > 1 else None,
        'next_page': page + 1 if page < pages else None
    }

@recettes_bp.route('/', methods=['GET', 'POST'])
def liste():
    if request.method == 'POST':
        nom = request.form.get('nom')
        instructions = request.form.get('instructions')
        type_recette = request.form.get('type_recette')
        temps_preparation = request.form.get('temps_preparation')
        
        recette = Recette(
            nom=nom, 
            instructions=instructions,
            type_recette=type_recette if type_recette else None,
            temps_preparation=int(temps_preparation) if temps_preparation else None
        )
        
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(f"rec_{nom}_{file.filename}")
                filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                file.save(os.path.join(current_app.root_path, filepath))
                recette.image = filepath
        
        db.session.add(recette)
        db.session.commit()
        
        # Ajouter les ingrédients
        i = 0
        while True:
            ing_id = request.form.get(f'ingredient_{i}')
            if not ing_id:
                break
            quantite = float(request.form.get(f'quantite_{i}', 0))
            
            if ing_id and quantite > 0:
                ing_recette = IngredientRecette(
                    recette_id=recette.id,
                    ingredient_id=int(ing_id),
                    quantite=quantite
                )
                db.session.add(ing_recette)
            i += 1
        
        # Ajouter les étapes
        j = 0
        while True:
            etape_desc = request.form.get(f'etape_desc_{j}')
            if not etape_desc:
                break
            
            duree = request.form.get(f'etape_duree_{j}')
            duree_minutes = int(duree) if duree and duree.strip() else None
            
            if etape_desc.strip():
                etape = EtapeRecette(
                    recette_id=recette.id,
                    ordre=j + 1,
                    description=etape_desc.strip(),
                    duree_minutes=duree_minutes
                )
                db.session.add(etape)
            j += 1
        
        db.session.commit()
        flash(f'Recette "{nom}" créée avec succès !', 'success')
        return redirect(url_for('recettes.detail', id=recette.id))
    
    # Gestion de la recherche et pagination
    search_query = request.args.get('search', '')
    type_filter = request.args.get('type', '')
    ingredient_filter = request.args.get('ingredient', '')
    view_mode = request.args.get('view', 'grid')
    page = request.args.get('page', 1, type=int)
    
    query = Recette.query
    
    if search_query:
        query = query.filter(Recette.nom.ilike(f'%{search_query}%'))
    
    if type_filter:
        query = query.filter(Recette.type_recette == type_filter)
    
    if ingredient_filter:
        query = query.join(IngredientRecette).filter(
            IngredientRecette.ingredient_id == ingredient_filter
        )
    
    query = query.order_by(Recette.nom)
    
    # Paginer les résultats
    pagination = paginate_query(query, page, ITEMS_PER_PAGE)
    
    ingredients = Ingredient.query.order_by(Ingredient.nom).all()
    
    types_count = {}
    for type_rec in TYPES_RECETTES:
        count = Recette.query.filter_by(type_recette=type_rec).count()
        if count > 0:
            types_count[type_rec] = count
    
    return render_template('recettes.html', 
                         recettes=pagination['items'],
                         pagination=pagination,
                         ingredients=ingredients,
                         types_recettes=TYPES_RECETTES,
                         types_count=types_count,
                         search_query=search_query,
                         type_filter=type_filter,
                         ingredient_filter=ingredient_filter,
                         view_mode=view_mode)

@recettes_bp.route('/api/recettes')
def api_recettes():
    """API pour le lazy loading"""
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('search', '')
    type_filter = request.args.get('type', '')
    ingredient_filter = request.args.get('ingredient', '')
    
    query = Recette.query
    
    if search_query:
        query = query.filter(Recette.nom.ilike(f'%{search_query}%'))
    
    if type_filter:
        query = query.filter(Recette.type_recette == type_filter)
    
    if ingredient_filter:
        query = query.join(IngredientRecette).filter(
            IngredientRecette.ingredient_id == int(ingredient_filter)
        )
    
    query = query.order_by(Recette.nom)
    pagination = paginate_query(query, page, ITEMS_PER_PAGE)
    
    recettes_data = []
    for recette in pagination['items']:
        cout = recette.calculer_cout()
        nutrition = recette.calculer_nutrition()
        
        recettes_data.append({
            'id': recette.id,
            'nom': recette.nom,
            'type_recette': recette.type_recette,
            'temps_preparation': recette.temps_preparation,
            'image': recette.image,
            'nb_ingredients': len(recette.ingredients),
            'cout': cout,
            'nutrition': nutrition
        })
    
    return jsonify({
        'recettes': recettes_data,
        'pagination': {
            'page': pagination['page'],
            'pages': pagination['pages'],
            'total': pagination['total'],
            'has_next': pagination['has_next']
        }
    })

@recettes_bp.route('/<int:id>')
def detail(id):
    recette = Recette.query.get_or_404(id)
    cout_estime = recette.calculer_cout()
    nutrition = recette.calculer_nutrition()
    
    return render_template('recette_detail.html', recette=recette, cout_estime=cout_estime, nutrition=nutrition)

@recettes_bp.route('/modifier/<int:id>', methods=['GET', 'POST'])
def modifier(id):
    recette = Recette.query.get_or_404(id)
    
    if request.method == 'POST':
        recette.nom = request.form.get('nom')
        recette.type_recette = request.form.get('type_recette')
        temps_prep = request.form.get('temps_preparation')
        recette.temps_preparation = int(temps_prep) if temps_prep else None
        
        # Image
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename != '' and allowed_file(file.filename):
                if recette.image:
                    try:
                        os.remove(os.path.join(current_app.root_path, recette.image))
                    except:
                        pass
                
                filename = secure_filename(f"rec_{recette.nom}_{file.filename}")
                filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                file.save(os.path.join(current_app.root_path, filepath))
                recette.image = filepath
        
        # Supprimer les anciennes étapes
        for etape in recette.etapes:
            db.session.delete(etape)
        
        # Ajouter les nouvelles étapes
        j = 0
        while True:
            etape_desc = request.form.get(f'etape_desc_{j}')
            if not etape_desc:
                break
            
            duree = request.form.get(f'etape_duree_{j}')
            duree_minutes = int(duree) if duree and duree.strip() else None
            
            if etape_desc.strip():
                etape = EtapeRecette(
                    recette_id=recette.id,
                    ordre=j + 1,
                    description=etape_desc.strip(),
                    duree_minutes=duree_minutes
                )
                db.session.add(etape)
            j += 1
        
        db.session.commit()
        flash(f'Recette "{recette.nom}" modifiée !', 'success')
        return redirect(url_for('recettes.detail', id=recette.id))
    
    ingredients = Ingredient.query.order_by(Ingredient.nom).all()
    return render_template('recette_modifier.html', 
                         recette=recette, 
                         ingredients=ingredients,
                         types_recettes=TYPES_RECETTES)

@recettes_bp.route('/supprimer/<int:id>')
def supprimer(id):
    recette = Recette.query.get_or_404(id)
    nom = recette.nom
    
    planifications = RecettePlanifiee.query.filter_by(recette_id=id).all()
    
    if planifications:
        nb_planifications = len(planifications)
        flash(f'Attention : Cette recette a {nb_planifications} planification(s) associée(s). '
              f'Elles seront également supprimées.', 'info')
        
        for plan in planifications:
            db.session.delete(plan)
    
    if recette.image:
        try:
            os.remove(os.path.join(current_app.root_path, recette.image))
        except:
            pass
    
    db.session.delete(recette)
    db.session.commit()
    flash(f'Recette "{nom}" supprimée !', 'success')
    return redirect(url_for('recettes.liste'))
