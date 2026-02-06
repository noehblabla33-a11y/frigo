"""
utils/courses.py (VERSION CORRIGÉE)
Gestion des courses et de la planification de recettes

CORRECTION DU BUG :
Le bug venait du calcul de la quantité à ajouter à la liste de courses.
La quantité manquante (quantite_a_ajouter) était calculée correctement MAIS
le calcul du coût utilisait le prix_unitaire mal interprété.

ATTENTION : Le prix_unitaire est stocké en €/unité native :
- Pour un avocat (unité='pièce', prix=2€) : prix_unitaire = 2.0 (€/pièce)
- Pour de la farine (unité='g', prix=1.50€/kg) : prix_unitaire = 0.0015 (€/g)

Le problème était que la quantité_a_ajouter était correcte mais le calcul
du coût pouvait créer des confusions d'affichage.
"""

from models.models import db, Recette, IngredientRecette, StockFrigo, ListeCourses


def ajouter_ingredients_manquants_courses(recette_id: int) -> dict:
    """
    Ajoute les ingrédients manquants d'une recette à la liste de courses.
    
    Cette fonction :
    1. Récupère tous les ingrédients de la recette
    2. Pour chaque ingrédient, vérifie le stock disponible dans le frigo
    3. Calcule la quantité manquante (quantité requise - stock disponible)
    4. Ajoute cette quantité à la liste de courses (ou met à jour si déjà présent)
    
    Les quantités sont TOUJOURS en unités natives de l'ingrédient :
    - 2 avocats → quantite = 2.0
    - 500g de farine → quantite = 500.0
    - 250ml de lait → quantite = 250.0
    
    Args:
        recette_id: L'ID de la recette à planifier
    
    Returns:
        dict avec les clés:
            - ajoutes: Nombre d'ingrédients nouvellement ajoutés
            - maj: Nombre d'ingrédients dont la quantité a été augmentée
            - cout_total: Coût estimé des ingrédients ajoutés
    """
    recette = Recette.query.get(recette_id)
    if not recette:
        return {'ajoutes': 0, 'maj': 0, 'cout_total': 0}
    
    ajoutes = 0
    maj = 0
    cout_total = 0.0
    
    for ing_rec in recette.ingredients:
        ingredient_id = ing_rec.ingredient_id
        quantite_requise = ing_rec.quantite  # Quantité en unité native
        
        # Vérifier le stock disponible dans le frigo
        stock = StockFrigo.query.filter_by(ingredient_id=ingredient_id).first()
        quantite_disponible = stock.quantite if stock else 0
        
        # Calculer la quantité manquante
        # ✅ C'est ici que le calcul est crucial : on compare des unités natives
        quantite_manquante = quantite_requise - quantite_disponible
        
        if quantite_manquante > 0:
            # L'ingrédient est-il déjà dans la liste de courses (non acheté) ?
            course_existante = ListeCourses.query.filter_by(
                ingredient_id=ingredient_id,
                achete=False
            ).first()
            
            if course_existante:
                # Augmenter la quantité existante
                course_existante.quantite += quantite_manquante
                maj += 1
            else:
                # Ajouter un nouvel item à la liste de courses
                nouvelle_course = ListeCourses(
                    ingredient_id=ingredient_id,
                    quantite=quantite_manquante,  # ✅ Quantité en unité native
                    achete=False
                )
                db.session.add(nouvelle_course)
                ajoutes += 1
            
            cout_total += ing_rec.ingredient.calculer_prix(quantite_manquante)
    
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
        recette_id: L'ID de la recette dont on annule la planification
    
    Returns:
        dict avec les clés:
            - supprimes: Nombre d'items complètement supprimés
            - reduits: Nombre d'items dont la quantité a été réduite
    """
    recette = Recette.query.get(recette_id)
    if not recette:
        return {'supprimes': 0, 'reduits': 0}
    
    supprimes = 0
    reduits = 0
    
    for ing_rec in recette.ingredients:
        ingredient_id = ing_rec.ingredient_id
        quantite_recette = ing_rec.quantite
        
        # Chercher l'ingrédient dans la liste de courses (non acheté)
        course = ListeCourses.query.filter_by(
            ingredient_id=ingredient_id,
            achete=False
        ).first()
        
        if course:
            # Réduire la quantité ou supprimer
            if course.quantite <= quantite_recette:
                # Supprimer complètement
                db.session.delete(course)
                supprimes += 1
            else:
                # Réduire la quantité
                course.quantite -= quantite_recette
                reduits += 1
    
    return {
        'supprimes': supprimes,
        'reduits': reduits
    }


def deduire_ingredients_frigo(recette_id: int) -> int:
    """
    Déduit les ingrédients d'une recette du stock du frigo.
    
    Utilisé lorsqu'une recette planifiée est marquée comme préparée.
    
    Args:
        recette_id: L'ID de la recette préparée
    
    Returns:
        int: Nombre d'ingrédients déduits du stock
    """
    recette = Recette.query.get(recette_id)
    if not recette:
        return 0
    
    nb_deduits = 0
    
    for ing_rec in recette.ingredients:
        ingredient_id = ing_rec.ingredient_id
        quantite_a_deduire = ing_rec.quantite
        
        # Récupérer le stock
        stock = StockFrigo.query.filter_by(ingredient_id=ingredient_id).first()
        
        if stock and stock.quantite > 0:
            # Déduire la quantité (ne pas aller en négatif)
            stock.quantite = max(0, stock.quantite - quantite_a_deduire)
            nb_deduits += 1
            
            # Supprimer le stock s'il est à zéro
            if stock.quantite == 0:
                db.session.delete(stock)
    
    return nb_deduits
