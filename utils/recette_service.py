"""
utils/recette_service.py
Service layer pour la création et modification de recettes
"""
from models.models import db, Recette, IngredientRecette, EtapeRecette
from utils.files import save_uploaded_file, delete_file
from utils.forms import parse_recette_form, parse_ingredients_list, parse_etapes_list


def sauvegarder_ingredients(recette_id: int, form_data: dict):
    """
    Remplace les ingrédients d'une recette depuis les données du formulaire.

    Paramètres:
        recette_id: ID de la recette
        form_data: Données du formulaire (request.form)
    """
    IngredientRecette.query.filter_by(recette_id=recette_id).delete()

    for ing_id, quantite in parse_ingredients_list(form_data):
        db.session.add(IngredientRecette(
            recette_id=recette_id,
            ingredient_id=ing_id,
            quantite=quantite
        ))


def sauvegarder_etapes(recette_id: int, form_data: dict):
    """
    Remplace les étapes d'une recette depuis les données du formulaire.

    Paramètres:
        recette_id: ID de la recette
        form_data: Données du formulaire (request.form)
    """
    EtapeRecette.query.filter_by(recette_id=recette_id).delete()

    for ordre, (description, duree_minutes) in enumerate(parse_etapes_list(form_data), start=1):
        db.session.add(EtapeRecette(
            recette_id=recette_id,
            ordre=ordre,
            description=description,
            duree_minutes=duree_minutes
        ))


def gerer_image_recette(recette: Recette, files: dict):
    """
    Gère l'upload/remplacement de l'image d'une recette.

    Paramètres:
        recette: Instance de la recette
        files: Dictionnaire request.files
    """
    if 'image' not in files:
        return

    file = files['image']
    if not file or not file.filename:
        return

    if recette.image:
        delete_file(recette.image)

    filepath = save_uploaded_file(file, prefix=f'rec_{recette.nom}')
    if filepath:
        recette.image = filepath


def creer_recette(form_data: dict, files: dict) -> Recette:
    """
    Crée une nouvelle recette complète (métadonnées + ingrédients + étapes + image).

    Paramètres:
        form_data: Données du formulaire (request.form)
        files: Fichiers uploadés (request.files)

    Retour:
        Recette: L'instance créée

    Raises:
        ValueError: Si les données sont invalides
    """
    recette_data = parse_recette_form(form_data)
    recette = Recette(**recette_data)

    db.session.add(recette)
    db.session.flush()

    gerer_image_recette(recette, files)
    sauvegarder_ingredients(recette.id, form_data)
    sauvegarder_etapes(recette.id, form_data)

    return recette


def modifier_recette(recette: Recette, form_data: dict, files: dict):
    """
    Met à jour une recette existante (métadonnées + ingrédients + étapes + image).

    Paramètres:
        recette: Instance existante de la recette
        form_data: Données du formulaire (request.form)
        files: Fichiers uploadés (request.files)

    Raises:
        ValueError: Si les données sont invalides
    """
    recette_data = parse_recette_form(form_data)

    recette.nom = recette_data['nom']
    recette.instructions = recette_data['instructions']
    recette.type_recette = recette_data['type_recette']
    recette.temps_preparation = recette_data['temps_preparation']
    recette.temps_cuisson = recette_data['temps_cuisson']

    gerer_image_recette(recette, files)
    sauvegarder_ingredients(recette.id, form_data)
    sauvegarder_etapes(recette.id, form_data)
