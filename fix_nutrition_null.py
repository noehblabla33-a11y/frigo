from app import create_app
from models.models import db, Ingredient

app = create_app()

with app.app_context():
    # Récupérer tous les ingrédients
    ingredients = Ingredient.query.all()
    
    count = 0
    for ing in ingredients:
        updated = False
        
        if ing.calories is None:
            ing.calories = 0
            updated = True
        if ing.proteines is None:
            ing.proteines = 0
            updated = True
        if ing.glucides is None:
            ing.glucides = 0
            updated = True
        if ing.lipides is None:
            ing.lipides = 0
            updated = True
        if ing.fibres is None:
            ing.fibres = 0
            updated = True
        if ing.sucres is None:
            ing.sucres = 0
            updated = True
        if ing.sel is None:
            ing.sel = 0
            updated = True
        
        if updated:
            count += 1
    
    db.session.commit()
    print(f"✅ {count} ingrédient(s) mis à jour avec des valeurs nutritionnelles par défaut (0)")
    print(f"📊 Total d'ingrédients dans la base : {len(ingredients)}")
