"""
utils/courses.py (VERSION CORRIGÉE)
Fonctions utilitaires pour la gestion des courses et du stock

CORRECTIONS:
- ✅ CORRIGÉ: Bug dans deduire_ingredients_frigo où 'stock' n'était pas défini
- Utilise retirer_du_stock depuis utils/stock.py pour la cohérence
- Code optimisé et factorisé
"""
from models.models import db, Recette, IngredientRecette, ListeCourses, StockFrigo
from sqlalchemy.orm import joinedload


def ajouter_ingredients_manquants_courses(recette_id: int) -> dict:
    """
    Ajoute les ingrédients manquants d'une recette à la liste de courses.
    
    Compare les ingrédients de la recette avec le stock du frigo et ajoute
    uniquement les quantités manquantes à la liste de courses.
    
    Args:
        recette_id: ID de la recette
    
    Returns:
        dict avec:
            - ajoutes: nombre d'ingrédients ajoutés
            - maj: nombre d'ingrédients mis à jour (quantité augmentée)
            - cout_total: coût estimé des ingrédients ajoutés
    """
    recette = Recette.query.options(
        joinedload(Recette.ingredients).joinedload(IngredientRecette.ingredient)
    ).get(recette_id)
    
    if not recette:
        return {'ajoutes': 0, 'maj': 0, 'cout_total': 0}
    
    ajoutes = 0
    maj = 0
    cout_total = 0
    
    for ing_recette in recette.ingredients:
        ingredient = ing_recette.ingredient
        quantite_requise = ing_recette.quantite
        
        # Vérifier le stock disponible
        stock = StockFrigo.query.filter_by(ingredient_id=ingredient.id).first()
        quantite_en_stock = stock.quantite if stock else 0
        
        # Calculer la quantité manquante
        quantite_manquante = max(0, quantite_requise - quantite_en_stock)
        
        if quantite_manquante > 0:
            # Vérifier si l'ingrédient est déjà dans la liste de courses
            item_existant = ListeCourses.query.filter_by(
                ingredient_id=ingredient.id,
                achete=False
            ).first()
            
            if item_existant:
                # Augmenter la quantité
                item_existant.quantite += quantite_manquante
                maj += 1
            else:
                # Ajouter un nouvel article
                nouvel_item = ListeCourses(
                    ingredient_id=ingredient.id,
                    quantite=quantite_manquante
                )
                db.session.add(nouvel_item)
                ajoutes += 1
            
            # Calculer le coût
            if ingredient.prix_unitaire and ingredient.prix_unitaire > 0:
                cout_total += quantite_manquante * ingredient.prix_unitaire
    
    return {
        'ajoutes': ajoutes,
        'maj': maj,
        'cout_total': round(cout_total, 2)
    }


def retirer_ingredients_courses(recette_id: int) -> dict:
    """
    Retire les ingrédients d'une recette de la liste de courses.
    
    Utilisé lors de l'annulation d'une planification.
    
    Args:
        recette_id: ID de la recette
    
    Returns:
        dict avec:
            - supprimes: nombre d'articles supprimés
            - reduits: nombre d'articles dont la quantité a été réduite
    """
    recette = Recette.query.options(
        joinedload(Recette.ingredients).joinedload(IngredientRecette.ingredient)
    ).get(recette_id)
    
    if not recette:
        return {'supprimes': 0, 'reduits': 0}
    
    supprimes = 0
    reduits = 0
    
    for ing_recette in recette.ingredients:
        # Chercher l'article dans la liste de courses (non acheté)
        item = ListeCourses.query.filter_by(
            ingredient_id=ing_recette.ingredient_id,
            achete=False
        ).first()
        
        if item:
            # Réduire la quantité ou supprimer
            nouvelle_quantite = item.quantite - ing_recette.quantite
            
            if nouvelle_quantite <= 0:
                db.session.delete(item)
                supprimes += 1
            else:
                item.quantite = nouvelle_quantite
                reduits += 1
    
    return {'supprimes': supprimes, 'reduits': reduits}


def deduire_ingredients_frigo(recette_id: int) -> int:
    """
    Déduit les ingrédients utilisés d'une recette du stock du frigo.
    
    Appelée lorsqu'une recette planifiée est marquée comme préparée.
    
    Args:
        recette_id: ID de la recette préparée
    
    Returns:
        int: Nombre d'ingrédients déduits du stock
    
    ✅ CORRIGÉ: Import de retirer_du_stock et gestion correcte de la variable stock
    """
    from utils.stock import retirer_du_stock
    
    recette = Recette.query.options(
        joinedload(Recette.ingredients).joinedload(IngredientRecette.ingredient)
    ).get(recette_id)
    
    if not recette:
        return 0
    
    nb_deduits = 0
    
    for ing_recette in recette.ingredients:
        ingredient_id = ing_recette.ingredient_id
        quantite_a_deduire = ing_recette.quantite
        
        # ✅ CORRIGÉ: Utiliser retirer_du_stock au lieu de manipuler stock directement
        # Cela évite le bug "NameError: name 'stock' is not defined"
        result_stock, nouvelle_quantite = retirer_du_stock(ingredient_id, quantite_a_deduire)
        
        if result_stock is not None:
            nb_deduits += 1
    
    return nb_deduits
