from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from models.models import db, Recette, Ingredient, IngredientRecette, RecettePlanifiee
from werkzeug.utils import secure_filename
import os

recettes_bp = Blueprint('recettes', __name__)

TYPES_RECETTES = [
    'Entrée', 'Plat principal', 'Accompagnement', 'Dessert', 'Petit-déjeuner',
    'Salade', 'Soupe', 'Au four', 'À la poêle', 'À la casserole',
    'Sans cuisson', 'Boisson', 'Autre'
]

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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
        
        db.session.commit()
        flash(f'Recette "{nom}" créée avec succès !', 'success')
        return redirect(url_for('recettes.detail', id=recette.id))
    
    # Gestion de la recherche
    search_query = request.args.get('search', '')
    type_filter = request.args.get('type', '')
    ingredient_filter = request.args.get('ingredient', '')
    view_mode = request.args.get('view', 'grid')  # Nouveau : 'grid' ou 'list'
    
    query = Recette.query
    
    if search_query:
        query = query.filter(Recette.nom.ilike(f'%{search_query}%'))
    
    if type_filter:
        query = query.filter(Recette.type_recette == type_filter)
    
    if ingredient_filter:
        query = query.join(IngredientRecette).filter(
            IngredientRecette.ingredient_id == ingredient_filter
        )
    
    recettes = query.order_by(Recette.nom).all()
    ingredients = Ingredient.query.order_by(Ingredient.nom).all()
    
    types_count = {}
    for type_rec in TYPES_RECETTES:
        count = Recette.query.filter_by(type_recette=type_rec).count()
        if count > 0:
            types_count[type_rec] = count
    
    return render_template('recettes.html', 
                         recettes=recettes, 
                         ingredients=ingredients,
                         types_recettes=TYPES_RECETTES,
                         types_count=types_count,
                         search_query=search_query,
                         type_filter=type_filter,
                         ingredient_filter=ingredient_filter,
                         view_mode=view_mode)

@recettes_bp.route('/<int:id>')
def detail(id):
    recette = Recette.query.get_or_404(id)
    cout_estime = recette.calculer_cout()
    return render_template('recette_detail.html', recette=recette, cout_estime=cout_estime)

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
