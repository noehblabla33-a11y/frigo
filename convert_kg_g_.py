"""
Script de conversion : kg → g pour tous les ingrédients
ATTENTION: Ce script modifie la base de données !
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from app import create_app
from models.models import db, Ingredient, IngredientRecette

app = create_app()

with app.app_context():
    print("=" * 60)
    print("CONVERSION KG → G")
    print("=" * 60)
    
    # Trouver tous les ingrédients en kg
    ingredients_kg = Ingredient.query.filter_by(unite='kg').all()
    
    print(f"\n📊 Ingrédients à convertir: {len(ingredients_kg)}")
    
    if len(ingredients_kg) == 0:
        print("\n✅ Aucun ingrédient en kg, tout est déjà bon !")
    else:
        print("\nIngrédients qui seront convertis:")
        for ing in ingredients_kg:
            print(f"   - {ing.nom} (actuellement en kg)")
        
        # Demander confirmation
        print("\n⚠️  ATTENTION:")
        print("   - Les unités passeront de 'kg' à 'g'")
        print("   - Les quantités dans les recettes seront MULTIPLIÉES par 1000")
        print("   - Exemple: 0.2 kg → 200 g")
        print("   - Les valeurs nutritionnelles (kcal/100g) ne changent PAS")
        
        reponse = input("\nContinuer ? (oui/non): ").strip().lower()
        
        if reponse == 'oui':
            print("\n🔄 Conversion en cours...")
            
            for ing in ingredients_kg:
                print(f"\n   Conversion de '{ing.nom}':")
                
                # 1. Convertir l'unité
                print(f"      Unité: kg → g")
                ing.unite = 'g'
                
                # 2. Convertir les quantités dans TOUTES les recettes qui utilisent cet ingrédient
                recettes_liees = IngredientRecette.query.filter_by(ingredient_id=ing.id).all()
                
                if recettes_liees:
                    print(f"      Mise à jour de {len(recettes_liees)} recette(s):")
                    for ing_rec in recettes_liees:
                        ancienne_quantite = ing_rec.quantite
                        nouvelle_quantite = ing_rec.quantite * 1000  # kg → g
                        ing_rec.quantite = nouvelle_quantite
                        print(f"         - {ing_rec.recette.nom}: {ancienne_quantite} kg → {nouvelle_quantite} g")
                else:
                    print(f"      Pas de recettes utilisant cet ingrédient")
            
            # Sauvegarder les modifications
            db.session.commit()
            
            print("\n✅ Conversion terminée avec succès !")
            print("\n📊 Résumé:")
            print(f"   - {len(ingredients_kg)} ingrédient(s) converti(s)")
            print(f"   - Toutes les recettes ont été mises à jour")
            print(f"   - Les calculs nutritionnels devraient maintenant fonctionner !")
            
        else:
            print("\n❌ Conversion annulée.")
    
    print("\n" + "=" * 60)
    print("VÉRIFICATION FINALE")
    print("=" * 60)
    
    # Afficher un résumé des unités
    from collections import Counter
    
    all_ingredients = Ingredient.query.all()
    unites_count = Counter([ing.unite for ing in all_ingredients])
    
    print("\nRépartition des unités:")
    for unite, count in unites_count.items():
        print(f"   {unite}: {count} ingrédient(s)")
    
    print("\n" + "=" * 60)
