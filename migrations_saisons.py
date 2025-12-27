"""
migrations_saisons.py
Script de migration pour ajouter le système de saisons

À exécuter après avoir créé les modèles :
1. flask --app manage.py db migrate -m "Ajout système de saisons"
2. flask --app manage.py db upgrade

Ce fichier contient également un script pour initialiser les saisons
par défaut pour les ingrédients courants.
"""

# Données de saisons par défaut pour les ingrédients courants
# Format: nom_ingredient -> [liste_saisons]
# Les saisons sont : 'printemps', 'ete', 'automne', 'hiver'

SAISONS_INGREDIENTS = {
    # Légumes
    'tomate': ['ete'],
    'tomates': ['ete'],
    'courgette': ['ete'],
    'courgettes': ['ete'],
    'aubergine': ['ete'],
    'aubergines': ['ete'],
    'poivron': ['ete'],
    'poivrons': ['ete'],
    'concombre': ['ete'],
    'concombres': ['ete'],
    'melon': ['ete'],
    'pastèque': ['ete'],
    'haricot vert': ['ete'],
    'haricots verts': ['ete'],
    
    'carotte': ['automne', 'hiver', 'printemps'],
    'carottes': ['automne', 'hiver', 'printemps'],
    'poireau': ['automne', 'hiver'],
    'poireaux': ['automne', 'hiver'],
    'chou': ['automne', 'hiver'],
    'chou-fleur': ['automne', 'hiver'],
    'brocoli': ['automne', 'hiver'],
    'épinard': ['printemps', 'automne'],
    'épinards': ['printemps', 'automne'],
    'navet': ['automne', 'hiver'],
    'navets': ['automne', 'hiver'],
    'butternut': ['automne', 'hiver'],
    'courge': ['automne', 'hiver'],
    'potiron': ['automne', 'hiver'],
    'potimarron': ['automne', 'hiver'],
    'céleri': ['automne', 'hiver'],
    'betterave': ['automne', 'hiver'],
    'betteraves': ['automne', 'hiver'],
    'endive': ['hiver'],
    'endives': ['hiver'],
    'mâche': ['hiver'],
    
    'asperge': ['printemps'],
    'asperges': ['printemps'],
    'petit pois': ['printemps'],
    'petits pois': ['printemps'],
    'artichaut': ['printemps', 'ete'],
    'artichauts': ['printemps', 'ete'],
    'radis': ['printemps', 'ete'],
    'salade': ['printemps', 'ete'],
    'laitue': ['printemps', 'ete'],
    
    # Fruits
    'fraise': ['printemps', 'ete'],
    'fraises': ['printemps', 'ete'],
    'framboise': ['ete'],
    'framboises': ['ete'],
    'cerise': ['printemps', 'ete'],
    'cerises': ['printemps', 'ete'],
    'abricot': ['ete'],
    'abricots': ['ete'],
    'pêche': ['ete'],
    'pêches': ['ete'],
    'nectarine': ['ete'],
    'nectarines': ['ete'],
    'prune': ['ete'],
    'prunes': ['ete'],
    'raisin': ['automne'],
    'raisins': ['automne'],
    'figue': ['ete', 'automne'],
    'figues': ['ete', 'automne'],
    'pomme': ['automne', 'hiver'],
    'pommes': ['automne', 'hiver'],
    'poire': ['automne', 'hiver'],
    'poires': ['automne', 'hiver'],
    'coing': ['automne'],
    'coings': ['automne'],
    'châtaigne': ['automne'],
    'châtaignes': ['automne'],
    'noix': ['automne'],
    'noisette': ['automne'],
    'noisettes': ['automne'],
    'orange': ['hiver'],
    'oranges': ['hiver'],
    'clémentine': ['hiver'],
    'clémentines': ['hiver'],
    'mandarine': ['hiver'],
    'mandarines': ['hiver'],
    'citron': ['hiver'],
    'citrons': ['hiver'],
    'pamplemousse': ['hiver'],
    'kiwi': ['hiver'],
    'kiwis': ['hiver'],
    'rhubarbe': ['printemps'],
    
    # Herbes aromatiques
    'basilic': ['ete'],
    'menthe': ['ete'],
    'coriandre': ['ete'],
    'persil': ['printemps', 'ete', 'automne'],
    'ciboulette': ['printemps', 'ete'],
    'thym': ['printemps', 'ete', 'automne', 'hiver'],  # Toute l'année
    'romarin': ['printemps', 'ete', 'automne', 'hiver'],  # Toute l'année
    'laurier': ['printemps', 'ete', 'automne', 'hiver'],  # Toute l'année
}


def init_saisons_for_ingredients(app, db):
    """
    Initialise les saisons pour les ingrédients existants.
    À appeler après la migration de la base de données.
    
    Usage:
        from app import create_app
        from models.models import db
        from migrations_saisons import init_saisons_for_ingredients
        
        app = create_app()
        with app.app_context():
            init_saisons_for_ingredients(app, db)
    """
    from models.models import Ingredient, IngredientSaison
    
    with app.app_context():
        ingredients = Ingredient.query.all()
        count = 0
        
        for ingredient in ingredients:
            nom_lower = ingredient.nom.lower().strip()
            
            if nom_lower in SAISONS_INGREDIENTS:
                saisons = SAISONS_INGREDIENTS[nom_lower]
                
                # Supprimer les anciennes saisons si existantes
                IngredientSaison.query.filter_by(ingredient_id=ingredient.id).delete()
                
                # Ajouter les nouvelles saisons
                for saison in saisons:
                    ing_saison = IngredientSaison(
                        ingredient_id=ingredient.id,
                        saison=saison
                    )
                    db.session.add(ing_saison)
                
                count += 1
        
        db.session.commit()
        print(f"✓ Saisons initialisées pour {count} ingrédients")
        return count


if __name__ == '__main__':
    print("Ce script doit être importé et utilisé avec l'application Flask.")
    print("\nUsage:")
    print("  from app import create_app")
    print("  from models.models import db")
    print("  from migrations_saisons import init_saisons_for_ingredients")
    print("")
    print("  app = create_app()")
    print("  with app.app_context():")
    print("      init_saisons_for_ingredients(app, db)")
