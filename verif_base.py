"""
Vérification rapide de la base de données - Version universelle
À exécuter depuis le dossier racine de votre projet
"""

import sys
import os

# Ajouter le répertoire courant au path
sys.path.insert(0, os.path.abspath('.'))

# Essayer différentes façons d'importer
try:
    from app import app
    print("✓ Import: from app import app")
except ImportError:
    try:
        from app import create_app
        app = create_app()
        print("✓ Import: from app import create_app")
    except ImportError:
        try:
            import app as app_module
            app = app_module.app
            print("✓ Import: import app")
        except:
            print("❌ Impossible d'importer l'application Flask")
            print("\nStructure de votre projet détectée:")
            for item in os.listdir('.'):
                if not item.startswith('.'):
                    print(f"  - {item}")
            print("\nComment lancez-vous normalement votre application?")
            sys.exit(1)

from models.models import db, Ingredient

with app.app_context():
    print("=" * 60)
    print("VÉRIFICATION BASE DE DONNÉES")
    print("=" * 60)
    
    # Chercher spécifiquement le boeuf haché
    print("\n1. Recherche 'boeuf haché':")
    boeuf = Ingredient.query.filter(Ingredient.nom.ilike('%boeuf%haché%')).first()
    
    if boeuf:
        print(f"   ✓ Trouvé: {boeuf.nom}")
        print(f"   Calories stockées: {boeuf.calories}")
        print(f"   Protéines: {boeuf.proteines}")
        print(f"   Glucides: {boeuf.glucides}")
        print(f"   Lipides: {boeuf.lipides}")
        
        if boeuf.calories == 0:
            print("\n   ⚠️  ATTENTION: Les calories sont à 0 dans la base!")
            print("   → Vous devez re-modifier l'ingrédient après avoir appliqué le correctif")
        else:
            print(f"\n   ✓ Les valeurs nutritionnelles sont bien enregistrées!")
    else:
        print("   ❌ Boeuf haché non trouvé")
        print("\n   Tous les ingrédients contenant 'boeuf':")
        all_boeuf = Ingredient.query.filter(Ingredient.nom.ilike('%boeuf%')).all()
        if all_boeuf:
            for b in all_boeuf:
                print(f"   - {b.nom}: {b.calories} kcal")
        else:
            print("   Aucun ingrédient contenant 'boeuf'")
    
    # Compter les ingrédients avec/sans valeurs nutritionnelles
    print("\n2. Statistiques globales:")
    total = Ingredient.query.count()
    avec_calories = Ingredient.query.filter(Ingredient.calories > 0).count()
    
    print(f"   Total ingrédients: {total}")
    print(f"   Avec calories > 0: {avec_calories}")
    print(f"   Sans calories: {total - avec_calories}")
    
    if avec_calories == 0:
        print("\n   ❌ PROBLÈME DÉTECTÉ:")
        print("   Aucun ingrédient n'a de valeurs nutritionnelles!")
        print("   → Le correctif sur routes/ingredients.py n'a peut-être pas été appliqué")
        print("   → OU l'application n'a pas été redémarrée")
        print("   → OU vous n'avez pas encore re-modifié les ingrédients")
    elif avec_calories < total:
        print(f"\n   ⚠️  {total - avec_calories} ingrédient(s) sans valeurs nutritionnelles")
        print("   → Pensez à les compléter pour des calculs précis")
    
    print("\n" + "=" * 60)
