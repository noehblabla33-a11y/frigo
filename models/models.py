from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Ingredient(db.Model):
    """Catalogue des ingrédients (référentiel permanent)"""
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False, unique=True)
    unite = db.Column(db.String(20), default='g')
    prix_unitaire = db.Column(db.Float, default=0)
    image = db.Column(db.String(200), nullable=True)
    categorie = db.Column(db.String(50), nullable=True)
    poids_piece = db.Column(db.Float, nullable=True)
    calories = db.Column(db.Float, default=0)        # kcal pour 100g/100ml
    proteines = db.Column(db.Float, default=0)       # g pour 100g/100ml
    glucides = db.Column(db.Float, default=0)        # g pour 100g/100ml
    lipides = db.Column(db.Float, default=0)         # g pour 100g/100ml
    fibres = db.Column(db.Float, default=0)          # g pour 100g/100ml
    sucres = db.Column(db.Float, default=0)          # g pour 100g/100ml
    sel = db.Column(db.Float, default=0)             # g pour 100g/100ml
    
    # Relations
    stock = db.relationship('StockFrigo', backref='ingredient', uselist=False, 
                           cascade='all, delete-orphan')

    def get_nutrition_for_quantity(self, quantite):
        """
        Calcule les valeurs nutritionnelles pour une quantité donnée
        Les valeurs sont stockées pour 100g/100ml
        """
        if quantite <= 0:
            return {
                'calories': 0,
                'proteines': 0,
                'glucides': 0,
                'lipides': 0,
                'fibres': 0,
                'sucres': 0,
                'sel': 0
            }
        
        # Convertir la quantité en base 100
        factor = quantite / 100.0
        
        return {
            'calories': round(self.calories * factor, 1),
            'proteines': round(self.proteines * factor, 1),
            'glucides': round(self.glucides * factor, 1),
            'lipides': round(self.lipides * factor, 1),
            'fibres': round(self.fibres * factor, 1),
            'sucres': round(self.sucres * factor, 1),
            'sel': round(self.sel * factor, 2)
        }
    
    def __repr__(self):
        return f'<Ingredient {self.nom}>'

class StockFrigo(db.Model):
    """Stock actuel dans le frigo"""
    id = db.Column(db.Integer, primary_key=True)
    ingredient_id = db.Column(db.Integer, db.ForeignKey('ingredient.id'), 
                             nullable=False, unique=True)
    quantite = db.Column(db.Float, default=0)
    date_ajout = db.Column(db.DateTime, default=datetime.utcnow)
    date_modification = db.Column(db.DateTime, default=datetime.utcnow, 
                                 onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<StockFrigo {self.ingredient.nom}: {self.quantite}>'

class Recette(db.Model):
    """Modèle pour les recettes"""
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    instructions = db.Column(db.Text)  # Gardé pour compatibilité
    image = db.Column(db.String(200), nullable=True)
    type_recette = db.Column(db.String(50), nullable=True)
    temps_preparation = db.Column(db.Integer, nullable=True)
    
    # Relations avec suppression en cascade
    ingredients = db.relationship('IngredientRecette', backref='recette', 
                                 cascade='all, delete-orphan')
    etapes = db.relationship('EtapeRecette', backref='recette', 
                            cascade='all, delete-orphan', 
                            order_by='EtapeRecette.ordre')
    planifications = db.relationship('RecettePlanifiee', backref='recette_ref', 
                                    cascade='all, delete-orphan')
    
    def calculer_cout(self):
        """Calcule le coût estimé de la recette"""
        cout_total = 0
        for ing_rec in self.ingredients:
            if ing_rec.ingredient.prix_unitaire > 0:
                cout_total += ing_rec.quantite * ing_rec.ingredient.prix_unitaire
        return round(cout_total, 2)

    def calculer_nutrition(self):
        """
        Calcule les valeurs nutritionnelles totales de la recette
        """
        nutrition = {
            'calories': 0,
            'proteines': 0,
            'glucides': 0,
            'lipides': 0,
            'fibres': 0,
            'sucres': 0,
            'sel': 0
        }
        
        for ing_rec in self.ingredients:
            ing_nutrition = ing_rec.ingredient.get_nutrition_for_quantity(ing_rec.quantite)
            for key in nutrition.keys():
                nutrition[key] += ing_nutrition[key]
        
        # Arrondir les résultats
        return {k: round(v, 1) for k, v in nutrition.items()}
    
    def __repr__(self):
        return f'<Recette {self.nom}>'

class EtapeRecette(db.Model):
    """Étapes de préparation d'une recette avec minuteurs optionnels"""
    id = db.Column(db.Integer, primary_key=True)
    recette_id = db.Column(db.Integer, db.ForeignKey('recette.id'), nullable=False)
    ordre = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text, nullable=False)
    duree_minutes = db.Column(db.Integer, nullable=True)  # Minuteur optionnel
    
    def __repr__(self):
        return f'<EtapeRecette {self.recette_id} - Étape {self.ordre}>'

class IngredientRecette(db.Model):
    """Table de liaison entre recettes et ingrédients"""
    id = db.Column(db.Integer, primary_key=True)
    recette_id = db.Column(db.Integer, db.ForeignKey('recette.id'), nullable=False)
    ingredient_id = db.Column(db.Integer, db.ForeignKey('ingredient.id'), nullable=False)
    quantite = db.Column(db.Float, nullable=False)
    
    # Relations
    ingredient = db.relationship('Ingredient', backref='recettes')
    
    def __repr__(self):
        return f'<IngredientRecette R:{self.recette_id} I:{self.ingredient_id}>'

class RecettePlanifiee(db.Model):
    """Modèle pour les recettes planifiées"""
    id = db.Column(db.Integer, primary_key=True)
    recette_id = db.Column(db.Integer, db.ForeignKey('recette.id', ondelete='CASCADE'), 
                          nullable=False)
    date_planification = db.Column(db.DateTime, default=datetime.utcnow)
    date_preparation = db.Column(db.DateTime, nullable=True)
    preparee = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f'<RecettePlanifiee {self.recette_id} - {self.date_planification}>'

class ListeCourses(db.Model):
    """Modèle pour la liste de courses"""
    id = db.Column(db.Integer, primary_key=True)
    ingredient_id = db.Column(db.Integer, db.ForeignKey('ingredient.id'), nullable=False)
    quantite = db.Column(db.Float, nullable=False)
    achete = db.Column(db.Boolean, default=False)
    
    # Relations
    ingredient = db.relationship('Ingredient', backref='courses')
    
    def __repr__(self):
        return f'<ListeCourses {self.ingredient_id}: {self.quantite}>'
