from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify
from sqlalchemy.orm import joinedload
from models.models import db, Recette, Ingredient, IngredientRecette, RecettePlanifiee, EtapeRecette, StockFrigo, ListeCourses
from constants import TYPES_RECETTES, valider_type_recette
from utils.pagination import paginate_query
from utils.files import save_uploaded_file, delete_file
from utils.courses import ajouter_ingredients_manquants_courses
import os

recettes_bp = Blueprint('recettes', __name__)


@recettes_bp.route('/', methods=['GET', 'POST'])
def liste():
    if request.method == 'POST':
        nom = request.form.get('nom')
        instructions = request.form.get('instructions')
        type_recette = request.form.get('type_recette')
        temps_preparation = request.form.get('temps_preparation')
        
        # Validation du type de recette avec fonction depuis constants.py
        if type_recette and not valider_type_recette(type_recette):
            flash(f'Type de recette invalide : {type_recette}', 'danger')
            return redirect(url_for('recettes.liste'))
        
        recette = Recette(
            nom=nom, 
            instructions=instructions,
            type_recette=type_recette if type_recette else None,
            temps_preparation=int(temps_preparation) if temps_preparation else None
        )
        
        # Gestion du fichier avec fonction factorisée
        if 'image' in request.files:
            file = request.files['image']
            filepath = save_uploaded_file(file, prefix=f'rec_{nom}')
            if filepath:
                recette.image = f'uploads/{filename}'
        
        db.session.add(recette)
        db.session.commit()
        
        # Ajouter les ingrédients
        i = 0
        while True:
            ing_id = request.form.get(f'ingredient_{i}')
            if not ing_id:
                break
            
            # Gérer la conversion avec chaîne vide
            quantite_str = request.form.get(f'quantite_{i}', '').strip()
            quantite = float(quantite_str) if quantite_str else 0.0
            
            if ing_id and quantite > 0:
                ing_recette = IngredientRecette(
                    recette_id=recette.id,
                    ingredient_id=ing_id,
                    quantite=quantite
                )
                db.session.add(ing_recette)
            i += 1
        
        # Ajouter les étapes avec durée optionnelle
        j = 0
        while True:
            etape_desc = request.form.get(f'etape_desc_{j}')
            if not etape_desc:
                break
            if etape_desc.strip():
                duree_str = request.form.get(f'etape_duree_{j}')
                duree = int(duree_str) if duree_str and duree_str.strip() else None
                
                etape = EtapeRecette(
                    recette_id=recette.id,
                    ordre=j + 1,
                    description=etape_desc,
                    duree_minutes=duree
                )
                db.session.add(etape)
            j += 1
        
        db.session.commit()
        flash(f'Recette "{nom}" créée !', 'success')
        return redirect(url_for('recettes.detail', id=recette.id))
    
    # ============================================
    # AFFICHAGE DE LA LISTE
    # ============================================
    
    # Gestion des filtres (correspondant au template)
    search_query = request.args.get('search', '')
    type_filter = request.args.get('type', '')
    ingredient_filter_str = request.args.get('ingredient', '')
    ingredient_filter = int(ingredient_filter_str) if ingredient_filter_str else None
    page = request.args.get('page', 1, type=int)
    
    # Récupérer ITEMS_PER_PAGE depuis la config Flask
    items_per_page = current_app.config.get('ITEMS_PER_PAGE_RECETTES', 20)
    
    # Construire la requête
    query = Recette.query.options(joinedload(Recette.ingredients).joinedload(IngredientRecette.ingredient))
    
    # Filtre par recherche
    if search_query:
        query = query.filter(Recette.nom.ilike(f'%{search_query}%'))
    
    # Filtre par type
    if type_filter:
        query = query.filter(Recette.type_recette == type_filter)
    
    # Filtre par ingrédient
    if ingredient_filter:
        query = query.join(IngredientRecette).filter(IngredientRecette.ingredient_id == ingredient_filter)
    
    # Trier par nom
    query = query.order_by(Recette.nom)
    
    # ✅ Paginer les résultats avec fonction factorisée
    pagination = paginate_query(query, page, items_per_page)
    
    # Récupérer tous les ingrédients pour le filtre
    ingredients = Ingredient.query.order_by(Ingredient.nom).all()
    
    return render_template('recettes.html', 
                         recettes=pagination['items'],
                         pagination=pagination,
                         ingredients=ingredients,
                         types_recettes=TYPES_RECETTES,
                         search_query=search_query,
                         type_filter=type_filter,
                         ingredient_filter=ingredient_filter)


@recettes_bp.route('/<int:id>')
def detail(id):
    recette = Recette.query.get_or_404(id)
    cout_estime = recette.calculer_cout()
    nutrition = recette.calculer_nutrition()
    
    return render_template('recette_detail.html', 
                         recette=recette, 
                         cout_estime=cout_estime, 
                         nutrition=nutrition)


@recettes_bp.route('/planifier-rapide/<int:id>', methods=['POST'])
def planifier_rapide(id):
    """Planifier rapidement une recette depuis la liste"""
    recette = Recette.query.get_or_404(id)
    
    # Créer la planification
    planifiee = RecettePlanifiee(recette_id=recette.id)
    db.session.add(planifiee)
    
    resultat = ajouter_ingredients_manquants_courses(recette.id)
    db.session.commit()

    nb_ajoutes = resultat['ajoutes']  # ✅ Accéder au dict
    nb_maj = resultat['maj']
    cout_total = resultat['cout_total']

    if nb_ajoutes > 0 or nb_maj > 0:
        msg_parts = []
        if nb_ajoutes > 0:
            msg_parts.append(f'{nb_ajoutes} ingrédient(s) ajouté(s)')
        if nb_maj > 0:
            msg_parts.append(f'{nb_maj} quantité(s) augmentée(s)')
        
        message = f'✓ "{recette.nom}" planifiée ! {" et ".join(msg_parts)} à la liste de courses.'
        if cout_total > 0:
            message += f' (≈ {cout_total:.2f}€)'
        
        flash(message, 'success')
    else:
        flash(f'✓ "{recette.nom}" planifiée ! Vous avez déjà tous les ingrédients.', 'success')
    
    return redirect(url_for('recettes.detail', id=recette.id))



@recettes_bp.route('/modifier/<int:id>', methods=['GET', 'POST'])
def modifier(id):
    recette = Recette.query.get_or_404(id)
    
    if request.method == 'POST':
        recette.nom = request.form.get('nom')
        recette.instructions = request.form.get('instructions')
        recette.type_recette = request.form.get('type_recette')
        temps_prep = request.form.get('temps_preparation')
        recette.temps_preparation = int(temps_prep) if temps_prep else None
        
        # Gestion de l'image avec fonctions factorisées
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename:
                # Supprimer l'ancienne image
                if recette.image:
                    delete_file(recette.image)
                
                # Sauvegarder la nouvelle
                filepath = save_uploaded_file(file, prefix=f'rec_{recette.nom}')
                if filepath:
                    recette.image = filepath
        
        # Mise à jour des ingrédients
        IngredientRecette.query.filter_by(recette_id=id).delete()
        
        i = 0
        while True:
            ing_id = request.form.get(f'ingredient_{i}')
            if not ing_id:
                break
            
            # Gérer la conversion avec chaîne vide
            quantite_str = request.form.get(f'quantite_{i}', '').strip()
            quantite = float(quantite_str) if quantite_str else 0.0
            
            if ing_id and quantite > 0:
                ing_recette = IngredientRecette(
                    recette_id=recette.id,
                    ingredient_id=ing_id,
                    quantite=quantite
                )
                db.session.add(ing_recette)
            i += 1
        
        # Mise à jour des étapes
        EtapeRecette.query.filter_by(recette_id=id).delete()
        
        j = 0
        while True:
            etape_desc = request.form.get(f'etape_desc_{j}')
            if not etape_desc:
                break
            if etape_desc.strip():
                etape = EtapeRecette(
                    recette_id=recette.id,
                    ordre=j + 1,
                    description=etape_desc
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
                         types_recettes=TYPES_RECETTES)  # ✅ Depuis constants.py


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
    
    # ✅ Supprimer l'image avec fonction factorisée
    if recette.image:
        delete_file(recette.image)
    
    db.session.delete(recette)
    db.session.commit()
    flash(f'Recette "{nom}" supprimée !', 'success')
    return redirect(url_for('recettes.liste'))


@recettes_bp.route('/cuisiner-avec-frigo')
def cuisiner_avec_frigo():
    """
    Affiche les recettes triées par pourcentage d'ingrédients disponibles
    ET les recettes planifiées (non préparées)
    """
    # Récupérer toutes les recettes
    recettes = Recette.query.all()
    
    # Calculer la disponibilité pour chaque recette
    recettes_avec_score = []
    for recette in recettes:
        disponibilite = recette.calculer_disponibilite_ingredients()
        recettes_avec_score.append({
            'recette': recette,
            'disponibilite': disponibilite
        })
    
    # Trier par pourcentage décroissant, puis par nombre d'ingrédients disponibles
    recettes_avec_score.sort(
        key=lambda x: (x['disponibilite']['pourcentage'], x['disponibilite']['score']),
        reverse=True
    )
    
    # Séparer les recettes réalisables immédiatement
    recettes_realisables = [r for r in recettes_avec_score if r['disponibilite']['realisable']]
    recettes_partielles = [r for r in recettes_avec_score if not r['disponibilite']['realisable']]
    
    # Récupérer les recettes planifiées (non préparées)
    planifiees = RecettePlanifiee.query.filter_by(preparee=False).all()
    
    return render_template('cuisiner_avec_frigo.html',
                         recettes_realisables=recettes_realisables,
                         recettes_partielles=recettes_partielles,
                         nb_realisables=len(recettes_realisables),
                         planifiees=planifiees)
