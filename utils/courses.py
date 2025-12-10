"""
Utilitaires pour la gestion de la liste de courses
Contient les fonctions communes utilisées par plusieurs routes
"""
from models.models import db, ListeCourses, StockFrigo, IngredientRecette

def ajouter_ingredients_manquants_courses(recette_id):
    """
    Ajoute les ingrédients manquants d'une recette à la liste de courses
    
    Args:
        recette_id: ID de la recette
        
    Returns:
        int: Nombre d'ingrédients ajoutés/mis à jour
    """
    ingredients_recette = IngredientRecette.query.filter_by(recette_id=recette_id).all()
    ingredients_modifies = 0
    
    for ing_rec in ingredients_recette:
        # Vérifier le stock disponible
        stock = StockFrigo.query.filter_by(ingredient_id=ing_rec.ingredient_id).first()
        quantite_disponible = stock.quantite if stock else 0
        
        # Calculer ce qui manque
        if quantite_disponible < ing_rec.quantite:
            manquant = ing_rec.quantite - quantite_disponible
            
            # Chercher si l'ingrédient est déjà dans la liste (non acheté)
            item = ListeCourses.query.filter_by(
                ingredient_id=ing_rec.ingredient_id,
                achete=False
            ).first()
            
            if item:
                # Ajouter à la quantité existante
                item.quantite += manquant
            else:
                # Créer un nouvel item
                item = ListeCourses(
                    ingredient_id=ing_rec.ingredient_id,
                    quantite=manquant
                )
                db.session.add(item)
            
            ingredients_modifies += 1
    
    return ingredients_modifies


def retirer_ingredients_courses(recette_id):
    """
    Retire les quantités d'ingrédients d'une recette de la liste de courses
    Supprime l'ingrédient si la quantité devient nulle ou négative
    
    Args:
        recette_id: ID de la recette
        
    Returns:
        dict: {'retires': int, 'supprimes': int} - Nombre d'ingrédients modifiés et supprimés
    """
    ingredients_recette = IngredientRecette.query.filter_by(recette_id=recette_id).all()
    
    ingredients_retires = 0
    ingredients_supprimes = 0
    
    for ing_rec in ingredients_recette:
        # Chercher l'ingrédient dans la liste de courses (non acheté)
        item_course = ListeCourses.query.filter_by(
            ingredient_id=ing_rec.ingredient_id,
            achete=False
        ).first()
        
        if item_course:
            # Retirer la quantité correspondante
            nouvelle_quantite = item_course.quantite - ing_rec.quantite
            
            if nouvelle_quantite <= 0:
                # Si la quantité devient nulle ou négative, supprimer l'item
                db.session.delete(item_course)
                ingredients_supprimes += 1
            else:
                # Sinon, simplement réduire la quantité
                item_course.quantite = nouvelle_quantite
                ingredients_retires += 1
    
    return {
        'retires': ingredients_retires,
        'supprimes': ingredients_supprimes
    }


def deduire_ingredients_frigo(recette_id):
    """
    Déduit les ingrédients d'une recette du stock du frigo
    
    Args:
        recette_id: ID de la recette
        
    Returns:
        int: Nombre d'ingrédients déduits
    """
    ingredients_recette = IngredientRecette.query.filter_by(recette_id=recette_id).all()
    ingredients_deduits = 0
    
    for ing_rec in ingredients_recette:
        stock = StockFrigo.query.filter_by(ingredient_id=ing_rec.ingredient_id).first()
        if stock:
            stock.quantite = max(0, stock.quantite - ing_rec.quantite)
            ingredients_deduits += 1
    
    return ingredients_deduits
