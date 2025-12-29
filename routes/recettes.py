from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify
from sqlalchemy.orm import joinedload
from models.models import db, Recette, Ingredient, IngredientRecette, RecettePlanifiee, EtapeRecette, StockFrigo, ListeCourses
from constants import TYPES_RECETTES, valider_type_recette
from utils.pagination import paginate_query
from utils.files import save_uploaded_file, delete_file
from utils.courses import ajouter_ingredients_manquants_courses
from utils.forms import parse_float, parse_int_or_none, clean_string_or_none,parse_ingredients_list, parse_etapes_list
from utils.validators import validate_unique_recette, validate_type_recette
from utils.recommandation import (MoteurRecommandation, get_historique_recettes_ids, get_cout_max_recettes, get_temps_max_recettes)
from utils.saisons import get_saison_actuelle
from constants import SAISONS
import os

recettes_bp = Blueprint('recettes', __name__)


@recettes_bp.route('/', methods=['GET', 'POST'])
def liste():
    if request.method == 'POST':
        nom = request.form.get('nom')
        instructions = clean_string_or_none(request.form.get('instructions'))
        type_recette = clean_string_or_none(request.form.get('type_recette'))
        temps_preparation = parse_int_or_none(request.form.get('temps_preparation'))
        
        # Validation du type de recette avec fonction depuis constants.py
        if not validate_type_recette(type_recette, TYPES_RECETTES):
            return redirect(url_for('recettes.liste'))

        if not validate_unique_recette(nom):
            return redirect(url_for('recettes.liste'))
        
        recette = Recette(
            nom=nom, 
            instructions=instructions,
            type_recette=type_recette,
            temps_preparation=temps_preparation
        )
        
        # Gestion du fichier avec fonction factorisée
        if 'image' in request.files:
            file = request.files['image']
            filepath = save_uploaded_file(file, prefix=f'rec_{nom}')
            if filepath:
                recette.image = filepath
        
        db.session.add(recette)
        db.session.commit()
        
        # Ajouter les ingrédients
        for ing_id, quantite in parse_ingredients_list(request.form):
            ing_recette = IngredientRecette(
                recette_id=recette.id,
                ingredient_id=ing_id,
                quantite=quantite
            )
            db.session.add(ing_recette)
        
        # Ajouter les étapes avec durée optionnelle
        for ordre, (description, duree_minutes) in enumerate(parse_etapes_list(request.form), start=1):
            etape = EtapeRecette(
                recette_id=recette.id,
                ordre=ordre,
                description=description,
                duree_minutes=duree_minutes
            )
            db.session.add(etape)
        
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
    
    next_url = request.form.get('next') or request.referrer or url_for('recettes.liste')
    return redirect(next_url)



@recettes_bp.route('/modifier/<int:id>', methods=['GET', 'POST'])
def modifier(id):
    recette = Recette.query.get_or_404(id)
    
    if request.method == 'POST':
        recette.nom = request.form.get('nom')
        recette.instructions = clean_string_or_none(request.form.get('instructions'))
        recette.type_recette = clean_string_or_none(request.form.get('type_recette'))
        recette.temps_preparation = parse_int_or_none(request.form.get('temps_preparation'))
        
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
        
        for ing_id, quantite in parse_ingredients_list(request.form):
            ing_recette = IngredientRecette(
                recette_id=recette.id,
                ingredient_id=ing_id,
                quantite=quantite
            )
            db.session.add(ing_recette)
        
        # Mise à jour des étapes
        EtapeRecette.query.filter_by(recette_id=id).delete()
        
        for ordre, (description, duree_minutes) in enumerate(parse_etapes_list(request.form), start=1):
            etape = EtapeRecette(
                recette_id=recette.id,
                ordre=ordre,
                description=description,
                duree_minutes=duree_minutes  # ✅ AJOUT
            )
            db.session.add(etape)
        
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
    Affiche les recommandations de recettes basées sur le frigo
    ET les recettes planifiées (non préparées)
    
    ✅ REFACTORISÉ : Utilise le système de recommandation
    """
    # ============================================
    # PARAMÈTRES DE LA REQUÊTE
    # ============================================
    saison = request.args.get('saison', get_saison_actuelle())
    type_filter = request.args.get('type', '')
    realisable_only = request.args.get('realisable') == '1'
    limit = request.args.get('limit', 20, type=int)
    
    # Poids des critères (depuis query string ou défauts orientés "frigo")
    poids_config = {
        'disponibilite': float(request.args.get('poids_disponibilite', 1.0)),
        'saison': float(request.args.get('poids_saison', 0.7)),
        'variete': float(request.args.get('poids_variete', 0.6)),
        'cout': float(request.args.get('poids_cout', 0.4)),
        'temps': float(request.args.get('poids_temps', 0.3)),
        'nutrition': float(request.args.get('poids_nutrition', 0.2))
    }
    
    # ============================================
    # CONFIGURATION DU MOTEUR DE RECOMMANDATION
    # ============================================
    moteur = MoteurRecommandation()
    
    # Contexte
    moteur.set_contexte(
        saison=saison,
        cout_max=get_cout_max_recettes(),
        temps_max=get_temps_max_recettes(),
        historique_recettes=get_historique_recettes_ids(14)
    )
    
    # Appliquer les poids
    moteur.configurer_criteres(poids_config)
    
    # ============================================
    # GÉNÉRATION DES RECOMMANDATIONS
    # ============================================
    recettes = Recette.query.options(
        joinedload(Recette.ingredients).joinedload(IngredientRecette.ingredient)
    ).all()
    
    recommandations = moteur.recommander(
        recettes,
        limit=limit,
        filtre_realisable=realisable_only,
        filtre_type=type_filter if type_filter else None
    )
    
    # Séparer les recettes réalisables pour les statistiques
    nb_realisables = sum(
        1 for r in recommandations 
        if r.meta.get('disponibilite', {}).get('realisable', False)
    )
    
    planifiees = RecettePlanifiee.query.filter_by(preparee=False).all()
    
    return render_template(
        'cuisiner_avec_frigo.html',
        recommandations=recommandations,
        criteres_config=moteur.get_config(),
        nb_realisables=nb_realisables,
        nb_total=len(recommandations),
        planifiees=planifiees,
        # Filtres
        saison=saison,
        saison_actuelle=get_saison_actuelle(),
        saisons=SAISONS,
        types_recettes=TYPES_RECETTES,
        type_filter=type_filter,
        realisable_only=realisable_only,
        limit=limit
    )
