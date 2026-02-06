"""
utils/queries.py
Shim de compatibilité — toutes les requêtes sont dans queries_optimized.py

Ce fichier existe uniquement pour ne pas casser les imports existants.
Pour tout nouveau code, importer directement depuis utils.queries_optimized.
"""
from utils.queries_optimized import (
    # Courses
    get_courses_non_achetees,
    get_course_by_ingredient,
    get_courses_by_category,
    get_historique_courses,
    nettoyer_courses_orphelines,
    # Recettes
    get_recettes_with_all_relations as get_recettes_avec_ingredients,
    get_recette_with_details as get_recette_complete,
    get_recettes_by_type as get_recettes_par_type,
    get_recettes_avec_ingredient,
    get_recettes_realisables,
    search_recettes,
    # Planification
    get_planifications_pending as get_recettes_planifiees,
    get_planifications_historique as get_historique_preparations,
    get_preparations_periode,
    # Ingrédients
    get_all_ingredients as get_ingredients_avec_stock,
    get_ingredients_in_stock as get_ingredients_en_stock,
    get_categories_count,
    get_ingredients_de_saison,
    # Statistiques
    get_stock_stats,
    get_recettes_stats,
    get_top_recettes,
    get_ingredients_plus_utilises,
    get_stats_periode,
)
