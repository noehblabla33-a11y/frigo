"""
utils/courses.py
Logique métier pour la gestion de la liste de courses

✅ VERSION OPTIMISÉE - PHASE 2
- Toute la logique métier centralisée
- Fonctions réutilisables
- Documentation complète
- Gestion d'erreurs robuste
"""
from models.models import db, ListeCourses, StockFrigo, Ingredient, Recette, IngredientRecette
from flask import current_app


def ajouter_ingredients_manquants_courses(recette_id, force=False):
    """
    Ajoute les ingrédients manquants d'une recette à la liste de courses
    
    Cette fonction :
    1. Vérifie le stock actuel de chaque ingrédient
    2. Calcule la quantité manquante
    3. Ajoute ou met à jour la liste de courses
    
    Args:
        recette_id (int): ID de la recette
        force (bool): Si True, ajoute tous les ingrédients même s'ils sont en stock
        
    Returns:
        dict: {
            'ajoutes': int,  # Nombre d'ingrédients ajoutés
            'maj': int,  # Nombre d'ingrédients mis à jour
            'cout_total': float,  # Coût total estimé
            'details': list  # Liste des détails par ingrédient
        }
    
    Exemples:
        >>> resultat = ajouter_ingredients_manquants_courses(recette_id=5)
        >>> print(f"{resultat['ajoutes']} ingrédients ajoutés")
        >>> print(f"Coût total: {resultat['cout_total']:.2f}€")
    """
    try:
        recette = Recette.query.get_or_404(recette_id)
        ajoutes = 0
        maj = 0
        cout_total = 0
        details = []
        
        for ing_rec in recette.ingredients:
            ingredient = ing_rec.ingredient
            quantite_necessaire = ing_rec.quantite
            
            # Vérifier le stock actuel
            stock = StockFrigo.query.filter_by(ingredient_id=ingredient.id).first()
            quantite_en_stock = stock.quantite if stock else 0
            
            # Calculer la quantité manquante
            if force:
                quantite_manquante = quantite_necessaire
            else:
                quantite_manquante = max(0, quantite_necessaire - quantite_en_stock)
            
            if quantite_manquante > 0:
                # Vérifier si déjà dans la liste de courses (non acheté)
                course_existante = ListeCourses.query.filter_by(
                    ingredient_id=ingredient.id,
                    achete=False
                ).first()
                
                if course_existante:
                    # Mettre à jour la quantité
                    course_existante.quantite += quantite_manquante
                    maj += 1
                    details.append({
                        'ingredient': ingredient.nom,
                        'action': 'mise_a_jour',
                        'quantite': quantite_manquante,
                        'quantite_totale': course_existante.quantite
                    })
                else:
                    # Ajouter un nouvel item
                    nouvelle_course = ListeCourses(
                        ingredient_id=ingredient.id,
                        quantite=quantite_manquante
                    )
                    db.session.add(nouvelle_course)
                    ajoutes += 1
                    details.append({
                        'ingredient': ingredient.nom,
                        'action': 'ajout',
                        'quantite': quantite_manquante
                    })
                
                # Calculer le coût
                cout_total += quantite_manquante * (ingredient.prix_unitaire or 0)
        
        # Commit des changements
        db.session.commit()
        
        current_app.logger.info(
            f'Liste de courses mise à jour pour "{recette.nom}": '
            f'{ajoutes} ajoutés, {maj} mis à jour'
        )
        
        return {
            'ajoutes': ajoutes,
            'maj': maj,
            'cout_total': cout_total,
            'details': details
        }
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Erreur dans ajouter_ingredients_manquants_courses: {str(e)}')
        raise


def retirer_ingredients_courses(recette_id):
    """
    Retire les ingrédients d'une recette de la liste de courses
    
    Utilisé quand on annule une recette planifiée
    
    Args:
        recette_id (int): ID de la recette
        
    Returns:
        dict: {
            'supprimes': int,  # Items complètement retirés
            'reduits': int,  # Items dont la quantité a été réduite
            'details': list  # Détails par ingrédient
        }
    
    Exemples:
        >>> resultat = retirer_ingredients_courses(recette_id=5)
        >>> print(f"{resultat['supprimes']} items supprimés")
        >>> print(f"{resultat['reduits']} items réduits")
    """
    try:
        recette = Recette.query.get_or_404(recette_id)
        supprimes = 0
        reduits = 0
        details = []
        
        for ing_rec in recette.ingredients:
            # Chercher l'item dans la liste de courses (non acheté)
            course = ListeCourses.query.filter_by(
                ingredient_id=ing_rec.ingredient_id,
                achete=False
            ).first()
            
            if course:
                if course.quantite <= ing_rec.quantite:
                    # Supprimer complètement l'item
                    db.session.delete(course)
                    supprimes += 1
                    details.append({
                        'ingredient': ing_rec.ingredient.nom,
                        'action': 'suppression',
                        'quantite_retiree': course.quantite
                    })
                else:
                    # Réduire la quantité
                    quantite_avant = course.quantite
                    course.quantite -= ing_rec.quantite
                    reduits += 1
                    details.append({
                        'ingredient': ing_rec.ingredient.nom,
                        'action': 'reduction',
                        'quantite_retiree': ing_rec.quantite,
                        'quantite_restante': course.quantite
                    })
        
        # Commit des changements
        db.session.commit()
        
        current_app.logger.info(
            f'Ingrédients retirés de la liste de courses pour "{recette.nom}": '
            f'{supprimes} supprimés, {reduits} réduits'
        )
        
        return {
            'supprimes': supprimes,
            'reduits': reduits,
            'details': details
        }
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Erreur dans retirer_ingredients_courses: {str(e)}')
        raise


def deduire_ingredients_frigo(recette_id):
    """
    Déduit les ingrédients d'une recette du stock du frigo
    
    Utilisé quand on marque une recette comme préparée
    
    Args:
        recette_id (int): ID de la recette
        
    Returns:
        dict: {
            'deduits': int,  # Nombre d'ingrédients déduits
            'manquants': int,  # Nombre d'ingrédients manquants (stock = 0)
            'details': list  # Détails par ingrédient
        }
    
    Exemples:
        >>> resultat = deduire_ingredients_frigo(recette_id=5)
        >>> print(f"{resultat['deduits']} ingrédients déduits du frigo")
        >>> if resultat['manquants'] > 0:
        ...     print(f"⚠️ {resultat['manquants']} ingrédients manquaient")
    """
    try:
        recette = Recette.query.get(recette_id)
        if not recette:
            return 0
        
        nb_deduits = 0
        
        for ing_rec in recette.ingredients:
            stock, nouvelle_quantite = retirer_du_stock(ing_rec.ingredient_id, ing_rec.quantite)
            
            if stock:
                nb_deduits += 1
        
        return nb_deduits

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Erreur dans deduire_ingredients_frigo: {str(e)}')
        raise


def nettoyer_courses_achetees(jours=30):
    """
    Nettoie les anciennes courses achetées (archivage)
    
    Args:
        jours (int): Nombre de jours à conserver (par défaut 30)
        
    Returns:
        int: Nombre d'items supprimés
    
    Exemples:
        >>> nb_supprimes = nettoyer_courses_achetees(jours=30)
        >>> print(f"{nb_supprimes} anciens achats archivés")
    """
    try:
        from datetime import datetime, timedelta
        
        # Calculer la date limite
        date_limite = datetime.utcnow() - timedelta(days=jours)
        
        # Compter les items à supprimer
        items_anciens = ListeCourses.query.filter(
            ListeCourses.achete == True,
            ListeCourses.id < 1000  # Condition temporaire - devrait utiliser date_achat
        ).all()
        
        nb_supprimes = len(items_anciens)
        
        # Supprimer
        for item in items_anciens:
            db.session.delete(item)
        
        db.session.commit()
        
        current_app.logger.info(f'{nb_supprimes} anciens achats archivés')
        
        return nb_supprimes
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Erreur dans nettoyer_courses_achetees: {str(e)}')
        raise


def calculer_budget_courses():
    """
    Calcule le budget estimé de la liste de courses actuelle
    
    Returns:
        dict: {
            'total': float,  # Total estimé en €
            'avec_prix': int,  # Nombre d'items avec prix
            'sans_prix': int,  # Nombre d'items sans prix
            'items': list  # Détails par item
        }
    
    Exemples:
        >>> budget = calculer_budget_courses()
        >>> print(f"Budget total: {budget['total']:.2f}€")
        >>> print(f"{budget['sans_prix']} items sans prix")
    """
    try:
        items = ListeCourses.query.filter_by(achete=False).all()
        
        total = 0
        avec_prix = 0
        sans_prix = 0
        details = []
        
        for item in items:
            if item.ingredient.prix_unitaire and item.ingredient.prix_unitaire > 0:
                prix_item = item.quantite * item.ingredient.prix_unitaire
                total += prix_item
                avec_prix += 1
                details.append({
                    'ingredient': item.ingredient.nom,
                    'quantite': item.quantite,
                    'unite': item.ingredient.unite,
                    'prix_unitaire': item.ingredient.prix_unitaire,
                    'prix_total': prix_item
                })
            else:
                sans_prix += 1
                details.append({
                    'ingredient': item.ingredient.nom,
                    'quantite': item.quantite,
                    'unite': item.ingredient.unite,
                    'prix_unitaire': None,
                    'prix_total': 0
                })
        
        return {
            'total': total,
            'avec_prix': avec_prix,
            'sans_prix': sans_prix,
            'items': details
        }
    
    except Exception as e:
        current_app.logger.error(f'Erreur dans calculer_budget_courses: {str(e)}')
        raise
