"""
routes/main.py
Route principale avec Dashboard Dynamique

✅ VERSION AMÉLIORÉE - Dashboard intelligent sur la page d'accueil
- Statistiques en temps réel (frigo, courses, recettes)
- Alertes de stock bas
- Suggestions de recettes personnalisées
- Activité récente
"""
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
    Page d'accueil avec Dashboard Dynamique.
    
    Affiche:
    - Statistiques globales (frigo, courses, recettes, planification)
    - Alertes de stock bas
    - Suggestions de recettes basées sur le stock et la saison
    - Activité récente
    - Recettes planifiées à venir
    """
    try:
        # Récupérer toutes les données du dashboard
        dashboard = get_dashboard_data()
        
        # Récupérer les recettes planifiées
        recettes_planifiees = get_recettes_planifiees_a_venir()
        
        return render_template(
            'index.html',
            dashboard=dashboard,
            recettes_planifiees=recettes_planifiees,
            # Fonctions utilitaires pour le template
            formater_valeur_euros=formater_valeur_euros,
            get_emoji_categorie=get_emoji_categorie,
            get_couleur_alerte=get_couleur_alerte
        )
    
    except Exception as e:
        current_app.logger.error(f'Erreur lors du chargement du dashboard: {str(e)}')
        # En cas d'erreur, afficher une version simplifiée
        return render_template('index_simple.html')


@main_bp.route('/api/dashboard/stats')
def api_dashboard_stats():
    """
    API endpoint pour rafraîchir les stats du dashboard en AJAX.
    Utile pour une mise à jour en temps réel sans recharger la page.
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
