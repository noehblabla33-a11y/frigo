"""
Script de correction des prix après conversion kg → g
Si vous avez déjà converti les unités mais pas les prix
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from app import create_app
from models.models import db, Ingredient

app = create_app()

with app.app_context():
    print("=" * 60)
    print("CORRECTION DES PRIX APRÈS CONVERSION KG → G")
    print("=" * 60)
    
    # Trouver tous les ingrédients en grammes avec un prix
    ingredients_g = Ingredient.query.filter_by(unite='g').filter(
        Ingredient.prix_unitaire > 0
    ).all()
    
    print(f"\n📊 Ingrédients en grammes avec un prix: {len(ingredients_g)}")
    
    if len(ingredients_g) == 0:
        print("\n✅ Aucun ingrédient à corriger !")
    else:
        print("\nExemples d'ingrédients (les 10 premiers):")
        for ing in ingredients_g[:10]:
            prix_probable_kg = ing.prix_unitaire * 1000
            print(f"   - {ing.nom}: {ing.prix_unitaire}€/g")
            print(f"      → Si c'était {prix_probable_kg}€/kg à l'origine, on va diviser par 1000")
        
        if len(ingredients_g) > 10:
            print(f"   ... et {len(ingredients_g) - 10} autre(s)")
        
        print("\n⚠️  ATTENTION:")
        print("   Ce script va DIVISER TOUS les prix par 1000")
        print("   Exemple: 15€/g → 0.015€/g")
        print("   Assurez-vous que c'est bien ce que vous voulez !")
        print("\n   Si certains ingrédients étaient déjà en grammes avec le bon prix,")
        print("   ils seront aussi divisés par 1000 (ce qui sera incorrect)")
        
        reponse = input("\nContinuer ? (oui/non): ").strip().lower()
        
        if reponse == 'oui':
            print("\n🔄 Correction en cours...")
            
            nb_corriges = 0
            for ing in ingredients_g:
                ancien_prix = ing.prix_unitaire
                nouveau_prix = ing.prix_unitaire / 1000
                ing.prix_unitaire = nouveau_prix
                nb_corriges += 1
                
                if nb_corriges <= 5:  # Afficher les 5 premiers
                    print(f"   {ing.nom}: {ancien_prix}€/g → {nouveau_prix}€/g")
            
            if nb_corriges > 5:
                print(f"   ... et {nb_corriges - 5} autre(s)")
            
            # Sauvegarder
            db.session.commit()
            
            print(f"\n✅ Correction terminée !")
            print(f"   {nb_corriges} prix corrigé(s)")
            
        else:
            print("\n❌ Correction annulée.")
    
    print("\n" + "=" * 60)
    print("VÉRIFICATION - Exemples de prix")
    print("=" * 60)
    
    # Afficher quelques exemples pour vérifier
    exemples = Ingredient.query.filter(Ingredient.prix_unitaire > 0).limit(10).all()
    
    print("\nPrix actuels (les 10 premiers ingrédients avec prix):")
    for ing in exemples:
        prix_au_kg = ing.prix_unitaire * 1000 if ing.unite == 'g' else ing.prix_unitaire
        print(f"   {ing.nom}: {ing.prix_unitaire}€/{ing.unite}")
        if ing.unite == 'g':
            print(f"      → équivaut à ~{prix_au_kg}€/kg")
    
    print("\n💡 Vérifiez que ces prix sont cohérents !")
    print("   Exemple de prix raisonnables au kg:")
    print("   - Boeuf haché: 10-20€/kg")
    print("   - Poulet: 8-15€/kg")
    print("   - Pâtes: 1-3€/kg")
    print("   - Tomates: 2-4€/kg")
    
    print("\n" + "=" * 60)
