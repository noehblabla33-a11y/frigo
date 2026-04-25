from flask import Blueprint, render_template, current_app
from utils.dashboard import (
    get_dashboard_data,
    get_recettes_planifiees_a_venir,
    formater_valeur_euros,
    get_emoji_categorie,
    get_couleur_alerte
)

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """
    Page d'accueil avec dashboard dynamique.

    Affiche les statistiques globales, les alertes de stock bas,
    les suggestions de recettes et l'activité récente.
    """
    try:
        dashboard = get_dashboard_data()

        recettes_planifiees = get_recettes_planifiees_a_venir()

        return render_template(
            'index.html',
            dashboard=dashboard,
            recettes_planifiees=recettes_planifiees,
            formater_valeur_euros=formater_valeur_euros,
            get_emoji_categorie=get_emoji_categorie,
            get_couleur_alerte=get_couleur_alerte
        )

    except Exception as e:
        current_app.logger.error(f'Erreur lors du chargement du dashboard: {str(e)}')
        return render_template('index_simple.html')


@main_bp.route('/api/dashboard/stats')
def api_dashboard_stats():
    """
    Endpoint AJAX pour rafraîchir les stats du dashboard sans recharger la page.
    """
    from flask import jsonify

    try:
        dashboard = get_dashboard_data()

        return jsonify({
            'success': True,
            'data': {
                'frigo': {
                    'nb_items': dashboard.stats_frigo.nb_items,
                    'valeur_totale': dashboard.stats_frigo.valeur_totale
                },
                'courses': {
                    'nb_items': dashboard.stats_courses.nb_items,
                    'cout_estime': dashboard.stats_courses.cout_estime
                },
                'recettes': {
                    'nb_total': dashboard.stats_recettes.nb_total,
                    'nb_realisables': dashboard.stats_recettes.nb_realisables,
                    'nb_planifiees': dashboard.stats_recettes.nb_planifiees
                },
                'activite': {
                    'recettes_semaine': dashboard.stats_activite.recettes_semaine,
                    'recettes_mois': dashboard.stats_activite.recettes_mois,
                    'cout_semaine': dashboard.stats_activite.cout_semaine,
                    'cout_mois': dashboard.stats_activite.cout_mois
                },
                'alertes': [
                    {
                        'ingredient': a.ingredient.nom,
                        'quantite': a.quantite_actuelle,
                        'seuil': a.seuil_alerte,
                        'unite': a.unite,
                        'pourcentage': a.pourcentage_restant
                    }
                    for a in dashboard.alertes_stock
                ],
                'suggestions': [
                    {
                        'id': s.recette.id,
                        'nom': s.recette.nom,
                        'score': s.score_disponibilite,
                        'manquants': s.nb_ingredients_manquants,
                        'cout': s.cout_estime,
                        'saison': s.est_de_saison,
                        'temps': s.temps_preparation
                    }
                    for s in dashboard.suggestions_recettes
                ]
            },
            'timestamp': dashboard.date_mise_a_jour.isoformat()
        })

    except Exception as e:
        current_app.logger.error(f'Erreur API dashboard: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 500
