"""
Migration : Ajout du champ temps_cuisson à la table Recette

À exécuter avec :
flask --app manage.py db migrate -m "Ajout temps_cuisson"
flask --app manage.py db upgrade

Ou manuellement avec ce script
"""

from flask import Flask
from models.models import db
from sqlalchemy import text

def add_temps_cuisson_column(app):
    """
    Ajoute la colonne temps_cuisson à la table recette
    """
    with app.app_context():
        try:
            # Vérifier si la colonne existe déjà
            result = db.session.execute(text(
                "SELECT COUNT(*) FROM pragma_table_info('recette') WHERE name='temps_cuisson'"
            ))
            exists = result.scalar() > 0
            
            if exists:
                print("✓ La colonne temps_cuisson existe déjà")
                return True
            
            # Ajouter la colonne
            db.session.execute(text(
                "ALTER TABLE recette ADD COLUMN temps_cuisson INTEGER"
            ))
            db.session.commit()
            
            print("✓ Colonne temps_cuisson ajoutée avec succès")
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"✗ Erreur lors de l'ajout de la colonne : {e}")
            return False


if __name__ == "__main__":
    from app import create_app
    
    app = create_app()
    
    print("=" * 50)
    print("MIGRATION : Ajout du champ temps_cuisson")
    print("=" * 50)
    
    success = add_temps_cuisson_column(app)
    
    if success:
        print("\n✓ Migration réussie !")
        print("\nVous pouvez maintenant utiliser le champ temps_cuisson dans vos recettes.")
    else:
        print("\n✗ La migration a échoué")
        print("Vérifiez les erreurs ci-dessus")
