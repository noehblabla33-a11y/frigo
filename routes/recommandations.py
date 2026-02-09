"""
routes/recommandations.py
Routes pour le système de recommandation de recettes

FONCTIONNALITÉS :
- Page de recommandations avec critères ajustables
- API JSON pour les recommandations
- Intégration avec le système de saisons existant
"""
from flask import Blueprint, render_template, request, jsonify, current_app
from sqlalchemy.orm import joinedload
from models.models import Recette, IngredientRecette
from utils.recommandation import (
    MoteurRecommandation,
    creer_moteur_recommandation_standard,
    get_historique_recettes_ids,
    get_cout_max_recettes,
    get_temps_max_recettes
)
from utils.saisons import get_saison_actuelle
from constants import TYPES_RECETTES, SAISONS_NOMS

recommandations_bp = Blueprint('recommandations', __name__)


def parse_poids_criteres(form_or_args) -> dict:
    """
    Parse les poids des critères depuis les paramètres de requête.
    
    Args:
        form_or_args: request.form ou request.args
    
    Returns:
        Dict {critere: poids}
    """
    criteres = ['saison', 'disponibilite', 'cout', 'temps', 'nutrition', 'variete']
    poids = {}
    
    for critere in criteres:
        key = f'poids_{critere}'
        value = form_or_args.get(key)
        if value is not None:
            try:
                poids[critere] = max(0.0, min(1.0, float(value)))
            except (ValueError, TypeError):
                pass
    
    return poids


@recommandations_bp.route('/')
def index():
    """
    Page principale des recommandations avec critères ajustables.
    """
    # Paramètres de filtrage
    type_filter = request.args.get('type', '')
    realisable_only = request.args.get('realisable') == '1'
    saison = request.args.get('saison', get_saison_actuelle())
    limit = request.args.get('limit', 20, type=int)
    
    # Poids des critères (depuis query string ou défauts)
    poids_criteres = parse_poids_criteres(request.args)
    
    # Créer et configurer le moteur
    moteur = creer_moteur_recommandation_standard(saison=saison)
    
    # Appliquer les poids personnalisés si fournis
    if poids_criteres:
        moteur.configurer_criteres(poids_criteres)
    else:
        # Configuration par défaut orientée saison
        moteur.configurer_criteres({
            'saison': 0.9,
            'disponibilite': 1.0,
            'variete': 0.6,
            'cout': 0.4,
            'temps': 0.3,
            'nutrition': 0.3
        })
    
    # Récupérer les recettes avec préchargement
    recettes = Recette.query.options(
        joinedload(Recette.ingredients).joinedload(IngredientRecette.ingredient)
    ).all()
    
    # Générer les recommandations
    recommandations = moteur.recommander(
        recettes,
        limit=limit,
        filtre_realisable=realisable_only,
        filtre_type=type_filter if type_filter else None
    )
    
    return render_template(
        'recommandations.html',
        recommandations=recommandations,
        criteres_config=moteur.get_config(),
        saison=saison,
        saison_actuelle=get_saison_actuelle(),
        saisons=SAISONS,
        types_recettes=TYPES_RECETTES,
        type_filter=type_filter,
        realisable_only=realisable_only,
        limit=limit
    )


@recommandations_bp.route('/api', methods=['GET', 'POST'])
def api_recommandations():
    """
    API JSON pour les recommandations.
    
    Query params / JSON body:
        - saison: Saison de référence (défaut: actuelle)
        - limit: Nombre de résultats (défaut: 10)
        - realisable: Filtrer recettes réalisables (0/1)
        - type: Filtrer par type de recette
        - poids_*: Poids des critères (0.0-1.0)
        
    Returns:
        JSON avec liste de recommandations
    """
    try:
        # Récupérer les paramètres selon la méthode
        if request.method == 'POST':
            data = request.get_json() or {}
            saison = data.get('saison', get_saison_actuelle())
            limit = data.get('limit', 10)
            realisable_only = data.get('realisable', False)
            type_filter = data.get('type')
            poids_criteres = data.get('criteres', {})
        else:
            saison = request.args.get('saison', get_saison_actuelle())
            limit = request.args.get('limit', 10, type=int)
            realisable_only = request.args.get('realisable') == '1'
            type_filter = request.args.get('type')
            poids_criteres = parse_poids_criteres(request.args)
        
        # Créer et configurer le moteur
        moteur = creer_moteur_recommandation_standard(saison=saison)
        
        if poids_criteres:
            moteur.configurer_criteres(poids_criteres)
        
        # Récupérer les recettes
        recettes = Recette.query.options(
            joinedload(Recette.ingredients).joinedload(IngredientRecette.ingredient)
        ).all()
        
        # Générer les recommandations
        recommandations = moteur.recommander(
            recettes,
            limit=limit,
            filtre_realisable=realisable_only,
            filtre_type=type_filter
        )
        
        # Formater la réponse
        result = []
        for reco in recommandations:
            recette = reco.recette
            result.append({
                'recette': {
                    'id': recette.id,
                    'nom': recette.nom,
                    'type_recette': recette.type_recette,
                    'temps_preparation': recette.temps_preparation,
                    'image': recette.image,
                    'nb_ingredients': len(recette.ingredients)
                },
                'score_total': reco.score_total,
                'scores_details': reco.scores_details,
                'meta': {
                    k: v for k, v in reco.meta.items() 
                    if k in ['saison', 'disponibilite', 'cout']
                }
            })
        
        return jsonify({
            'success': True,
            'count': len(result),
            'saison': saison,
            'criteres': moteur.get_config(),
            'recommandations': result
        })
    
    except Exception as e:
        current_app.logger.error(f'Erreur API recommandations: {str(e)}')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@recommandations_bp.route('/presets/<preset>')
def preset(preset: str):
    """
    Applique un preset de configuration et redirige vers la page.
    
    Presets disponibles:
        - saison: Maximise les ingrédients de saison
        - economique: Minimise le coût
        - rapide: Minimise le temps de préparation
        - frigo: Maximise l'utilisation du stock
        - equilibre: Configuration équilibrée
    """
    from flask import redirect, url_for
    
    presets = {
        'saison': {
            'poids_saison': '1.0',
            'poids_disponibilite': '0.7',
            'poids_variete': '0.5',
            'poids_cout': '0.3',
            'poids_temps': '0.2',
            'poids_nutrition': '0.3'
        },
        'economique': {
            'poids_cout': '1.0',
            'poids_disponibilite': '0.8',
            'poids_saison': '0.5',
            'poids_variete': '0.4',
            'poids_temps': '0.3',
            'poids_nutrition': '0.2'
        },
        'rapide': {
            'poids_temps': '1.0',
            'poids_disponibilite': '0.8',
            'poids_saison': '0.4',
            'poids_cout': '0.3',
            'poids_variete': '0.3',
            'poids_nutrition': '0.2'
        },
        'frigo': {
            'poids_disponibilite': '1.0',
            'poids_saison': '0.6',
            'poids_variete': '0.5',
            'poids_cout': '0.3',
            'poids_temps': '0.4',
            'poids_nutrition': '0.2',
            'realisable': '1'
        },
        'equilibre': {
            'poids_saison': '0.6',
            'poids_disponibilite': '0.6',
            'poids_variete': '0.6',
            'poids_cout': '0.6',
            'poids_temps': '0.6',
            'poids_nutrition': '0.6'
        }
    }
    
    params = presets.get(preset, presets['equilibre'])
    
    return redirect(url_for('recommandations.index', **params))
