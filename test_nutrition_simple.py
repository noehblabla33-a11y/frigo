"""
Test simple du calcul nutritionnel
À exécuter depuis le dossier de votre projet Flask: python test_nutrition_simple.py
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from app import create_app
from models.models import db, Ingredient, Recette, IngredientRecette

app = create_app()

with app.app_context():
    print("=" * 60)
    print("TEST SIMPLE - Boeuf haché à 250 kcal/100g, recette avec 200g")
    print("=" * 60)
    
    # Récupérer le boeuf haché
    boeuf = Ingredient.query.filter(Ingredient.nom.ilike('%boeuf%haché%')).first()
    
    if not boeuf:
        print("\n❌ PROBLÈME: Ingrédient 'boeuf haché' non trouvé!")
        print("   Ingrédients disponibles contenant 'boeuf':")
        boeufs = Ingredient.query.filter(Ingredient.nom.ilike('%boeuf%')).all()
        for b in boeufs:
            print(f"   - {b.nom}: {b.calories} kcal/100{b.unite}")
    else:
        print(f"\n✓ Boeuf haché trouvé: {boeuf.nom}")
        print(f"  Calories en base: {boeuf.calories} kcal/100{boeuf.unite}")
        print(f"  Protéines: {boeuf.proteines}g")
        print(f"  Glucides: {boeuf.glucides}g")
        print(f"  Lipides: {boeuf.lipides}g")
        
        # Test de la fonction get_nutrition_for_quantity
        print(f"\n📊 Test avec 200g:")
        nutrition_200g = boeuf.get_nutrition_for_quantity(200)
        print(f"  Résultat: {nutrition_200g}")
        print(f"  Calories: {nutrition_200g['calories']} (attendu: ~500)")
        
        # Trouver une recette qui utilise cet ingrédient
        print(f"\n🍳 Recherche de recettes utilisant {boeuf.nom}:")
        ing_recettes = IngredientRecette.query.filter_by(ingredient_id=boeuf.id).all()
        
        if not ing_recettes:
            print(f"  ❌ Aucune recette n'utilise {boeuf.nom}")
        else:
            print(f"  ✓ {len(ing_recettes)} recette(s) trouvée(s)")
            
            for ing_rec in ing_recettes[:1]:  # Tester la première
                recette = ing_rec.recette
                print(f"\n  Recette testée: {recette.nom}")
                print(f"  Quantité de boeuf: {ing_rec.quantite}{boeuf.unite}")
                
                # Calcul nutrition de la recette
                print(f"\n  📈 Calcul nutritionnel de la recette:")
                nutrition_recette = recette.calculer_nutrition()
                print(f"  Résultat: {nutrition_recette}")
                
                # Vérification manuelle
                print(f"\n  🔍 Vérification manuelle:")
                total = 0
                for ir in recette.ingredients:
                    ing_nut = ir.ingredient.get_nutrition_for_quantity(ir.quantite)
                    print(f"    - {ir.ingredient.nom} ({ir.quantite}{ir.ingredient.unite}):")
                    print(f"      Base: {ir.ingredient.calories} kcal/100{ir.ingredient.unite}")
                    print(f"      Contribution: {ing_nut['calories']} kcal")
                    total += ing_nut['calories']
                
                print(f"\n  Total manuel: {total} kcal")
                print(f"  Total fonction: {nutrition_recette['calories']} kcal")
                
                if abs(total - nutrition_recette['calories']) < 0.1:
                    print(f"  ✓ Les calculs correspondent!")
                else:
                    print(f"  ❌ PROBLÈME: Différence détectée!")
    
    print("\n" + "=" * 60)
