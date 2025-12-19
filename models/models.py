from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Ingredient(db.Model):
    """Catalogue des ingrédients (référentiel permanent)"""
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False, unique=True, index=True)
    unite = db.Column(db.String(20), default='g')
    prix_unitaire = db.Column(db.Float, default=0)
    image = db.Column(db.String(200), nullable=True)
    categorie = db.Column(db.String(50), nullable=True, index=True)
    poids_piece = db.Column(db.Float, nullable=True)
    calories = db.Column(db.Float, default=0)        # kcal pour 100g/100ml
    proteines = db.Column(db.Float, default=0)       # g pour 100g/100ml
    glucides = db.Column(db.Float, default=0)        # g pour 100g/100ml
    lipides = db.Column(db.Float, default=0)         # g pour 100g/100ml
    fibres = db.Column(db.Float, default=0)          # g pour 100g/100ml
    sucres = db.Column(db.Float, default=0)          # g pour 100g/100ml
    sel = db.Column(db.Float, default=0)             # g pour 100g/100ml
    
    # Relations
    stock = db.relationship('StockFrigo', backref=dbbackref('ingredient', lazy='joined'),
                            uselist=False, 
                            cascade='all, delete-orphan',
                            lazy='select')

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

    def to_dict(self, include_stock=False, include_nutrition=False):
        """
        Convertit l'ingrédient en dictionnaire pour JSON
        
        Args:
            include_stock: Inclure les infos de stock du frigo
            include_nutrition: Inclure les valeurs nutritionnelles
        
        Returns:
            dict: Données de l'ingrédient au format JSON
        """
        data = {
            'id': self.id,
            'nom': self.nom,
            'unite': self.unite,
            'prix_unitaire': self.prix_unitaire,
            'categorie': self.categorie,
            'image': self.image,
            'poids_piece': self.poids_piece
        }
        
        # Inclure le stock si demandé
        if include_stock:
            data['stock'] = {
                'en_stock': self.stock is not None and self.stock.quantite > 0,
                'quantite': self.stock.quantite if self.stock else 0,
                'date_modification': self.stock.date_modification.isoformat() if self.stock else None
            }
        
        # Inclure les valeurs nutritionnelles si demandé
        if include_nutrition:
            data['nutrition'] = {
                'calories': self.calories,
                'proteines': self.proteines,
                'glucides': self.glucides,
                'lipides': self.lipides,
                'fibres': self.fibres,
                'sucres': self.sucres,
                'sel': self.sel
            }
        
        return data
    
    def __repr__(self):
        return f'<Ingredient {self.nom}>'

class StockFrigo(db.Model):
    """Stock actuel dans le frigo"""
    id = db.Column(db.Integer, primary_key=True)
    ingredient_id = db.Column(db.Integer, db.ForeignKey('ingredient.id'), 
                             nullable=False, unique=True, index=True)
    quantite = db.Column(db.Float, default=0)
    date_ajout = db.Column(db.DateTime, default=datetime.utcnow)
    date_modification = db.Column(db.DateTime, default=datetime.utcnow, 
                                 onupdate=datetime.utcnow)

    def to_dict(self, include_ingredient=False):
        """
        Convertit le stock en dictionnaire pour JSON
        
        Args:
            include_ingredient: Inclure les détails de l'ingrédient
        
        Returns:
            dict: Données du stock au format JSON
        """
        data = {
            'id': self.id,
            'ingredient_id': self.ingredient_id,
            'ingredient_nom': self.ingredient.nom,
            'ingredient_unite': self.ingredient.unite,
            'quantite': self.quantite,
            'date_ajout': self.date_ajout.isoformat(),
            'date_modification': self.date_modification.isoformat()
        }
        
        # Inclure les détails complets de l'ingrédient si demandé
        if include_ingredient:
            data['ingredient'] = self.ingredient.to_dict()
        
        return data
    
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

    def calculer_disponibilite_ingredients(self):
        """
        Calcule le pourcentage d'ingrédients disponibles dans le frigo
        Retourne un dictionnaire avec les détails
        """
        if not self.ingredients:
            return {
                'pourcentage': 0,
                'ingredients_disponibles': [],
                'ingredients_manquants': [],
                'realisable': False
            }
        
        total_ingredients = len(self.ingredients)
        disponibles = []
        manquants = []
        
        for ing_rec in self.ingredients:
            stock = StockFrigo.query.filter_by(ingredient_id=ing_rec.ingredient_id).first()
            quantite_disponible = stock.quantite if stock else 0
            
            if quantite_disponible >= ing_rec.quantite:
                disponibles.append({
                    'ingredient': ing_rec.ingredient,
                    'quantite_requise': ing_rec.quantite,
                    'quantite_disponible': quantite_disponible
                })
            else:
                manquants.append({
                    'ingredient': ing_rec.ingredient,
                    'quantite_requise': ing_rec.quantite,
                    'quantite_disponible': quantite_disponible,
                    'quantite_manquante': ing_rec.quantite - quantite_disponible
                })
        
        pourcentage = (len(disponibles) / total_ingredients * 100) if total_ingredients > 0 else 0
        realisable = len(manquants) == 0
        
        return {
            'pourcentage': round(pourcentage, 1),
            'ingredients_disponibles': disponibles,
            'ingredients_manquants': manquants,
            'realisable': realisable,
            'score': len(disponibles)  # Pour le tri
        }


    def to_dict(self, include_ingredients=False, include_etapes=False, 
                include_nutrition=False, include_cout=False, include_disponibilite=False):
        """
        Convertit la recette en dictionnaire pour JSON
        
        Args:
            include_ingredients: Inclure la liste des ingrédients
            include_etapes: Inclure les étapes de préparation
            include_nutrition: Inclure les valeurs nutritionnelles
            include_cout: Inclure le coût estimé
            include_disponibilite: Inclure la disponibilité des ingrédients
        
        Returns:
            dict: Données de la recette au format JSON
        """
        data = {
            'id': self.id,
            'nom': self.nom,
            'instructions': self.instructions,
            'image': self.image,
            'type_recette': self.type_recette,
            'temps_preparation': self.temps_preparation
        }
        
        # Inclure les ingrédients si demandé
        if include_ingredients:
            data['ingredients'] = [
                {
                    'ingredient_id': ing_rec.ingredient_id,
                    'ingredient_nom': ing_rec.ingredient.nom,
                    'quantite': ing_rec.quantite,
                    'unite': ing_rec.ingredient.unite,
                    'prix_unitaire': ing_rec.ingredient.prix_unitaire
                }
                for ing_rec in self.ingredients
            ]
            data['nb_ingredients'] = len(self.ingredients)
        
        # Inclure les étapes si demandé
        if include_etapes:
            data['etapes'] = [
                {
                    'ordre': etape.ordre,
                    'description': etape.description,
                    'duree_minutes': etape.duree_minutes
                }
                for etape in self.etapes
            ]
            data['nb_etapes'] = len(self.etapes)
        
        # Inclure les valeurs nutritionnelles si demandé
        if include_nutrition:
            data['nutrition'] = self.calculer_nutrition()
        
        # Inclure le coût si demandé
        if include_cout:
            data['cout_estime'] = self.calculer_cout()
        
        # Inclure la disponibilité si demandé
        if include_disponibilite:
            data['disponibilite'] = self.calculer_disponibilite_ingredients()
        
        return data

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
    recette_id = db.Column(db.Integer, db.ForeignKey('recette.id'), nullable=False, index=True)
    ingredient_id = db.Column(db.Integer, db.ForeignKey('ingredient.id'), nullable=False, index=True)
    quantite = db.Column(db.Float, nullable=False)
    
    # Relations
    ingredient = db.relationship('Ingredient', backref='recettes')
    
    def __repr__(self):
        return f'<IngredientRecette R:{self.recette_id} I:{self.ingredient_id}>'

class RecettePlanifiee(db.Model):
    """Modèle pour les recettes planifiées"""
    id = db.Column(db.Integer, primary_key=True)
    recette_id = db.Column(db.Integer, db.ForeignKey('recette.id', ondelete='CASCADE'), 
                          nullable=False, index=True)
    date_planification = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    date_preparation = db.Column(db.DateTime, nullable=True)
    preparee = db.Column(db.Boolean, default=False, index=True)


    def to_dict(self, include_recette=False):
        """
        Convertit la recette planifiée en dictionnaire pour JSON
        
        Args:
            include_recette: Inclure les détails complets de la recette
        
        Returns:
            dict: Données de la planification au format JSON
        """
        data = {
            'id': self.id,
            'recette_id': self.recette_id,
            'recette_nom': self.recette_ref.nom,
            'date_planification': self.date_planification.isoformat(),
            'date_preparation': self.date_preparation.isoformat() if self.date_preparation else None,
            'preparee': self.preparee
        }
        
        # Inclure les détails de la recette si demandé
        if include_recette:
            data['recette'] = self.recette_ref.to_dict(
                include_ingredients=True,
                include_cout=True
            )
        
        return data

    
    def __repr__(self):
        return f'<RecettePlanifiee {self.recette_id} - {self.date_planification}>'

class ListeCourses(db.Model):
    """Modèle pour la liste de courses"""
    id = db.Column(db.Integer, primary_key=True)
    ingredient_id = db.Column(db.Integer, db.ForeignKey('ingredient.id'), nullable=False, index=True)
    quantite = db.Column(db.Float, nullable=False)
    achete = db.Column(db.Boolean, default=False, index=True)
    
    # Relations
    ingredient = db.relationship('Ingredient', backref='courses')

    def to_dict(self, include_ingredient=False):
        """
        Convertit l'item de course en dictionnaire pour JSON
        
        Args:
            include_ingredient: Inclure les détails de l'ingrédient
        
        Returns:
            dict: Données de l'item au format JSON
        """
        data = {
            'id': self.id,
            'ingredient_id': self.ingredient_id,
            'ingredient_nom': self.ingredient.nom,
            'ingredient_unite': self.ingredient.unite,
            'quantite': self.quantite,
            'achete': self.achete
        }
        
        # Inclure les détails complets de l'ingrédient si demandé
        if include_ingredient:
            data['ingredient'] = self.ingredient.to_dict()
        
        return data
    
    def __repr__(self):
        return f'<ListeCourses {self.ingredient_id}: {self.quantite}>'
