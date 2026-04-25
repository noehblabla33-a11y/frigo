from datetime import date, datetime
from typing import List, Optional, Dict, Tuple
from sqlalchemy import func
from models.models import db, Ingredient, Recette
from constants import SAISONS_NOMS, SAISONS_EMOJIS, SAISONS_VALIDES as ORDRE_SAISONS


def get_saison_actuelle(date_ref: date = None) -> str:
    """
    Détermine la saison actuelle basée sur la date.

    Args:
        date_ref: Date de référence (par défaut: aujourd'hui)

    Returns:
        Nom de la saison: 'printemps', 'ete', 'automne', ou 'hiver'
    """
    if date_ref is None:
        date_ref = date.today()

    jour = date_ref.day
    mois = date_ref.month

    date_num = mois * 100 + jour

    if 320 <= date_num < 621:
        return 'printemps'
    elif 621 <= date_num < 922:
        return 'ete'
    elif 922 <= date_num < 1221:
        return 'automne'
    else:
        return 'hiver'


def get_saison_suivante(saison: str = None) -> str:
    """
    Retourne la saison suivante.

    Args:
        saison: Saison actuelle (défaut: saison courante)

    Returns:
        Nom de la prochaine saison
    """
    if saison is None:
        saison = get_saison_actuelle()

    idx = ORDRE_SAISONS.index(saison)
    return ORDRE_SAISONS[(idx + 1) % 4]


def get_saison_precedente(saison: str = None) -> str:
    """
    Retourne la saison précédente.

    Args:
        saison: Saison actuelle (défaut: saison courante)

    Returns:
        Nom de la saison précédente
    """
    if saison is None:
        saison = get_saison_actuelle()

    idx = ORDRE_SAISONS.index(saison)
    return ORDRE_SAISONS[(idx - 1) % 4]


def formater_saison(saison: str, avec_emoji: bool = True) -> str:
    """
    Formate une saison pour l'affichage.

    Args:
        saison: Code de la saison
        avec_emoji: Inclure l'emoji

    Returns:
        Chaîne formatée (ex: "Printemps")
    """
    nom = get_saison_nom(saison)
    if avec_emoji:
        emoji = get_saison_emoji(saison)
        return f"{emoji} {nom}" if emoji else nom
    return nom


def formater_liste_saisons(saisons: list, avec_emoji: bool = True) -> str:
    """
    Formate une liste de saisons pour l'affichage.

    Args:
        saisons: Liste de codes de saisons
        avec_emoji: Inclure les emojis

    Returns:
        Chaîne formatée ou "Toute l'année"
    """
    if not saisons:
        return "Toute l'année"

    ordre = {s: i for i, s in enumerate(SAISONS_VALIDES)}
    saisons_triees = sorted(saisons, key=lambda s: ordre.get(s, 99))

    if len(saisons_triees) == 4:
        return "Toute l'année"

    return ", ".join(formater_saison(s, avec_emoji) for s in saisons_triees)


def get_ingredients_de_saison(saison: str = None, categorie: str = None) -> List[Ingredient]:
    """
    Récupère les ingrédients disponibles pour une saison donnée.

    Les ingrédients sans saisons définies (disponibles toute l'année)
    sont inclus dans les résultats.

    Args:
        saison: Saison à filtrer (défaut: saison actuelle)
        categorie: Filtrer par catégorie (optionnel)

    Returns:
        Liste d'ingrédients de saison
    """
    from models.models import IngredientSaison

    if saison is None:
        saison = get_saison_actuelle()

    ingredients_saison = db.session.query(IngredientSaison.ingredient_id)\
        .filter(IngredientSaison.saison == saison)\
        .subquery()

    ingredients_avec_saisons = db.session.query(IngredientSaison.ingredient_id.distinct())\
        .subquery()

    query = Ingredient.query.filter(
        db.or_(
            Ingredient.id.in_(ingredients_saison),
            ~Ingredient.id.in_(ingredients_avec_saisons)
        )
    )

    if categorie:
        query = query.filter(Ingredient.categorie == categorie)

    return query.order_by(Ingredient.nom).all()


def get_ingredients_hors_saison(saison: str = None) -> List[Ingredient]:
    """
    Récupère les ingrédients qui ne sont pas de saison.

    Args:
        saison: Saison de référence (défaut: saison actuelle)

    Returns:
        Liste d'ingrédients hors saison
    """
    from models.models import IngredientSaison

    if saison is None:
        saison = get_saison_actuelle()

    ingredients_saison = db.session.query(IngredientSaison.ingredient_id)\
        .filter(IngredientSaison.saison == saison)\
        .subquery()

    ingredients_avec_saisons = db.session.query(IngredientSaison.ingredient_id.distinct())\
        .subquery()

    return Ingredient.query.filter(
        Ingredient.id.in_(ingredients_avec_saisons),
        ~Ingredient.id.in_(ingredients_saison)
    ).order_by(Ingredient.nom).all()


def compter_ingredients_par_saison() -> Dict[str, int]:
    """
    Compte le nombre d'ingrédients par saison.

    Returns:
        Dict {saison: count}
    """
    from models.models import IngredientSaison

    result = db.session.query(
        IngredientSaison.saison,
        func.count(IngredientSaison.ingredient_id.distinct())
    ).group_by(IngredientSaison.saison).all()

    return {saison: count for saison, count in result}


def calculer_score_saisonnier_recette(recette: Recette, saison: str = None) -> Dict:
    """
    Calcule le score saisonnier d'une recette.

    Le score représente le pourcentage d'ingrédients de saison dans la recette.

    Args:
        recette: Recette à évaluer
        saison: Saison de référence (défaut: saison actuelle)

    Returns:
        Dict avec score, ingredients_saison, ingredients_hors_saison, ingredients_toute_annee
    """
    if saison is None:
        saison = get_saison_actuelle()

    if not recette.ingredients:
        return {
            'score': 0,
            'ingredients_saison': [],
            'ingredients_hors_saison': [],
            'ingredients_toute_annee': []
        }

    ingredients_saison = []
    ingredients_hors_saison = []
    ingredients_toute_annee = []

    for ing_rec in recette.ingredients:
        ingredient = ing_rec.ingredient
        saisons_ing = ingredient.get_saisons()

        if not saisons_ing:
            ingredients_toute_annee.append(ingredient)
        elif saison in saisons_ing:
            ingredients_saison.append(ingredient)
        else:
            ingredients_hors_saison.append(ingredient)

    total = len(recette.ingredients)
    positifs = len(ingredients_saison) + len(ingredients_toute_annee)
    score = round((positifs / total) * 100, 1) if total > 0 else 0

    return {
        'score': score,
        'ingredients_saison': ingredients_saison,
        'ingredients_hors_saison': ingredients_hors_saison,
        'ingredients_toute_annee': ingredients_toute_annee
    }


def get_recettes_de_saison(saison: str = None,
                           score_minimum: float = 80.0,
                           limit: int = None) -> List[Tuple[Recette, Dict]]:
    """
    Récupère les recettes adaptées à une saison.

    Args:
        saison: Saison de référence (défaut: saison actuelle)
        score_minimum: Score saisonnier minimum (0-100)
        limit: Nombre maximum de résultats

    Returns:
        Liste de tuples (recette, score_info) triée par score décroissant
    """
    if saison is None:
        saison = get_saison_actuelle()

    recettes = Recette.query.all()
    recettes_avec_score = []

    for recette in recettes:
        score_info = calculer_score_saisonnier_recette(recette, saison)
        if score_info['score'] >= score_minimum:
            recettes_avec_score.append((recette, score_info))

    recettes_avec_score.sort(key=lambda x: x[1]['score'], reverse=True)

    if limit:
        recettes_avec_score = recettes_avec_score[:limit]

    return recettes_avec_score


def get_recettes_recommandees(saison: str = None,
                              inclure_disponibilite: bool = True,
                              limit: int = 10) -> List[Dict]:
    """
    Recommandations de recettes combinant score saisonnier et disponibilité.

    Args:
        saison: Saison de référence (défaut: saison actuelle)
        inclure_disponibilite: Tenir compte du stock du frigo
        limit: Nombre maximum de recommandations

    Returns:
        Liste de dicts avec recette, scores et détails
    """
    if saison is None:
        saison = get_saison_actuelle()

    recettes = Recette.query.all()
    recommandations = []

    for recette in recettes:
        score_saison = calculer_score_saisonnier_recette(recette, saison)

        if inclure_disponibilite:
            dispo = recette.calculer_disponibilite_ingredients()
            score_dispo = dispo['pourcentage']
        else:
            dispo = None
            score_dispo = 100

        score_combine = (score_saison['score'] * 0.6) + (score_dispo * 0.4)

        recommandations.append({
            'recette': recette,
            'score_combine': round(score_combine, 1),
            'score_saison': score_saison['score'],
            'score_disponibilite': score_dispo,
            'nb_ingredients_saison': len(score_saison['ingredients_saison']),
            'nb_ingredients_hors_saison': len(score_saison['ingredients_hors_saison']),
            'disponibilite': dispo
        })

    recommandations.sort(key=lambda x: x['score_combine'], reverse=True)

    return recommandations[:limit]


def get_contexte_saison() -> Dict:
    """
    Retourne un contexte complet pour les templates.

    Returns:
        Dict avec toutes les infos de saison utiles
    """
    saison_actuelle = get_saison_actuelle()

    return {
        'saison_actuelle': saison_actuelle,
        'saison_actuelle_nom': SAISONS_NOMS.get(saison_actuelle, ''),
        'saison_actuelle_emoji': SAISONS_EMOJIS.get(saison_actuelle, ''),
        'saison_suivante': get_saison_suivante(saison_actuelle),
        'toutes_saisons': ORDRE_SAISONS,
        'saisons_noms': SAISONS_NOMS,
        'saisons_emojis': SAISONS_EMOJIS,
    }


def get_saison_emoji(saison: str) -> str:
    """
    Retourne l'emoji pour une saison donnée.

    Args:
        saison: Code de la saison

    Returns:
        Emoji correspondant ou chaîne vide
    """
    return SAISONS_EMOJIS.get(saison, '')


def get_saison_nom(saison: str) -> str:
    """
    Retourne le nom complet d'une saison.

    Args:
        saison: Code de la saison

    Returns:
        Nom complet ou le code si non trouvé
    """
    return SAISONS_NOMS.get(saison, saison.capitalize() if saison else '')
