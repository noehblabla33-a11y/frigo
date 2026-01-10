"""
models/models.py
Modèles de données pour l'application Frigo

SYSTÈME D'UNITÉS REFACTORÉ :
- Les quantités sont stockées dans l'unité NATIVE de l'ingrédient
- Pour un œuf (unite='pièce'), on stocke 2 (pas 120g)
- Pour de la farine (unite='g'), on stocke 500
- Pour du lait (unite='ml'), on stocke 250

✅ NOUVEAU : Système de saisons pour les ingrédients
- Un ingrédient peut être associé à plusieurs saisons
- Les ingrédients sans saison sont disponibles toute l'année
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


# ============================================
# SAISONS DES INGRÉDIENTS
# ============================================

class IngredientSaison(db.Model):
    """
    Table d'association pour les saisons des ingrédients.
    Un ingrédient peut être disponible sur plusieurs saisons.
    
    Saisons possibles : 'printemps', 'ete', 'automne', 'hiver'
    
    Exemples:
        - Tomate -> ['ete'] (uniquement en été)
        - Carotte -> ['automne', 'hiver', 'printemps'] (sauf été)
        - Pomme de terre -> [] (toute l'année, pas de restriction)
    """
    __tablename__ = 'ingredient_saison'
    
    id = db.Column(db.Integer, primary_key=True)
    ingredient_id = db.Column(db.Integer, db.ForeignKey('ingredient.id', ondelete='CASCADE'), 
                             nullable=False, index=True)
    saison = db.Column(db.String(20), nullable=False, index=True)
    
    __table_args__ = (
        db.UniqueConstraint('ingredient_id', 'saison', name='uq_ingredient_saison'),
        db.Index('idx_ingredient_saison_composite', 'ingredient_id', 'saison'),
    )
    
    def __repr__(self):
        return f'<IngredientSaison {self.ingredient_id}:{self.saison}>'


# ============================================
# INGRÉDIENTS
# ============================================

class Ingredient(db.Model):
    """Catalogue des ingrédients (référentiel permanent)"""
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False, unique=True, index=True)
    unite = db.Column(db.String(20), default='g')
    prix_unitaire = db.Column(db.Float, default=0)
    image = db.Column(db.String(200), nullable=True)
    categorie = db.Column(db.String(50), nullable=True, index=True)
    poids_piece = db.Column(db.Float, nullable=True)
    
    # Valeurs nutritionnelles pour 100g ou 100ml
    calories = db.Column(db.Float, default=0)
    proteines = db.Column(db.Float, default=0)
    glucides = db.Column(db.Float, default=0)
    lipides = db.Column(db.Float, default=0)
    fibres = db.Column(db.Float, default=0)
    sucres = db.Column(db.Float, default=0)
    sel = db.Column(db.Float, default=0)
    
    # Relations
    stock = db.relationship('StockFrigo', backref=db.backref('ingredient', lazy='joined'),
                            uselist=False, 
                            cascade='all, delete-orphan',
                            lazy='select')
    
    # ✅ NOUVEAU : Relation vers les saisons
    saisons = db.relationship('IngredientSaison', 
                             backref='ingredient_ref',
                             cascade='all, delete-orphan',
                             lazy='select')

    # ============================================
    # MÉTHODES DE CONVERSION
    # ============================================

    def get_quantite_en_grammes(self, quantite_native: float) -> float:
        """Convertit une quantité en unité native vers grammes."""
        if quantite_native <= 0:
            return 0
        
        if self.unite == 'pièce' and self.poids_piece and self.poids_piece > 0:
            return quantite_native * self.poids_piece
        
        return quantite_native

    def get_nutrition_for_quantity(self, quantite_native: float) -> dict:
        """Calcule les valeurs nutritionnelles pour une quantité donnée."""
        if quantite_native <= 0:
            return {
                'calories': 0, 'proteines': 0, 'glucides': 0,
                'lipides': 0, 'fibres': 0, 'sucres': 0, 'sel': 0
            }
        
        quantite_grammes = self.get_quantite_en_grammes(quantite_native)
        factor = quantite_grammes / 100.0
        
        # Helper pour gérer les valeurs NULL
        def calc_value(val, decimals=1):
            """Calcule la valeur nutritionnelle en gérant NULL"""
            return round((val or 0) * factor, decimals) if val is not None else 0
        
        return {
            'calories': calc_value(self.calories),
            'proteines': calc_value(self.proteines),
            'glucides': calc_value(self.glucides),
            'lipides': calc_value(self.lipides),
            'fibres': calc_value(self.fibres),
            'sucres': calc_value(self.sucres),
            'sel': calc_value(self.sel, 2)  # 2 décimales pour le sel
        }

    def calculer_prix(self, quantite_native: float) -> float:
        """Calcule le prix pour une quantité donnée."""
        if quantite_native <= 0 or not self.prix_unitaire or self.prix_unitaire <= 0:
            return 0
        return round(quantite_native * self.prix_unitaire, 2)

    # ============================================
    # ✅ MÉTHODES POUR LES SAISONS
    # ============================================

    def get_saisons(self) -> list:
        """
        Retourne la liste des saisons où l'ingrédient est disponible.
        
        Returns:
            Liste de saisons ['printemps', 'ete', 'automne', 'hiver'] ou []
            Une liste vide signifie "disponible toute l'année"
        """
        return [s.saison for s in self.saisons]

    def set_saisons(self, saisons: list):
        """
        Définit les saisons de disponibilité de l'ingrédient.
        
        Args:
            saisons: Liste de saisons valides ['printemps', 'ete', 'automne', 'hiver']
                     Une liste vide signifie "disponible toute l'année"
        """
        from constants import SAISONS_VALIDES
        
        # Valider les saisons
        for saison in saisons:
            if saison not in SAISONS_VALIDES:
                raise ValueError(f"Saison invalide: {saison}. Valides: {SAISONS_VALIDES}")
        
        # Supprimer les anciennes saisons
        IngredientSaison.query.filter_by(ingredient_id=self.id).delete()
        
        # Ajouter les nouvelles (sans doublons)
        for saison in set(saisons):
            ing_saison = IngredientSaison(ingredient_id=self.id, saison=saison)
            db.session.add(ing_saison)

    def est_de_saison(self, saison: str = None) -> bool:
        """
        Vérifie si l'ingrédient est de saison.
        
        Args:
            saison: Saison à vérifier. Si None, utilise la saison actuelle.
        
        Returns:
            True si de saison ou disponible toute l'année, False sinon
        """
        from utils.saisons import get_saison_actuelle
        
        saisons_ingredient = self.get_saisons()
        
        # Si pas de saisons définies, disponible toute l'année
        if not saisons_ingredient:
            return True
        
        if saison is None:
            saison = get_saison_actuelle()
        
        return saison in saisons_ingredient

    # ============================================
    # SÉRIALISATION
    # ============================================

    def to_dict(self, include_stock=False, include_nutrition=False, include_saisons=False):
        """Convertit l'ingrédient en dictionnaire pour JSON"""
        data = {
            'id': self.id,
            'nom': self.nom,
            'unite': self.unite,
            'prix_unitaire': self.prix_unitaire,
            'categorie': self.categorie,
            'image': self.image,
            'poids_piece': self.poids_piece
        }
        
        if include_stock:
            data['stock'] = {
                'en_stock': self.stock is not None and self.stock.quantite > 0,
                'quantite': self.stock.quantite if self.stock else 0,
                'date_modification': self.stock.date_modification.isoformat() if self.stock else None
            }
        
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
        
        # ✅ NOUVEAU : Inclure les saisons
        if include_saisons:
            data['saisons'] = self.get_saisons()
            data['est_de_saison'] = self.est_de_saison()
        
        return data
    
    def __repr__(self):
        return f'<Ingredient {self.nom}>'


# ============================================
# STOCK FRIGO
# ============================================

class StockFrigo(db.Model):
    """Stock actuel dans le frigo - quantités en unités natives"""
    id = db.Column(db.Integer, primary_key=True)
    ingredient_id = db.Column(db.Integer, db.ForeignKey('ingredient.id'), 
                             nullable=False, unique=True, index=True)
    quantite = db.Column(db.Float, default=0)
    date_ajout = db.Column(db.DateTime, default=datetime.utcnow)
    date_modification = db.Column(db.DateTime, default=datetime.utcnow, 
                                 onupdate=datetime.utcnow)

    def to_dict(self, include_ingredient=False):
        """Convertit le stock en dictionnaire pour JSON"""
        data = {
            'id': self.id,
            'ingredient_id': self.ingredient_id,
            'ingredient_nom': self.ingredient.nom,
            'ingredient_unite': self.ingredient.unite,
            'quantite': self.quantite,
            'date_ajout': self.date_ajout.isoformat(),
            'date_modification': self.date_modification.isoformat()
        }
        
        if include_ingredient:
            data['ingredient'] = self.ingredient.to_dict(include_saisons=True)
        
        return data
    
    def __repr__(self):
        return f'<StockFrigo {self.ingredient.nom}: {self.quantite}>'


# ============================================
# RECETTES
# ============================================

class Recette(db.Model):
    """Modèle pour les recettes"""
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    instructions = db.Column(db.Text)
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
    
    def calculer_cout(self) -> float:
        """Calcule le coût estimé de la recette."""
        cout_total = 0
        for ing_rec in self.ingredients:
            cout_total += ing_rec.ingredient.calculer_prix(ing_rec.quantite)
        return round(cout_total, 2)

    def calculer_nutrition(self) -> dict:
        """Calcule les valeurs nutritionnelles totales de la recette."""
        nutrition = {
            'calories': 0, 'proteines': 0, 'glucides': 0,
            'lipides': 0, 'fibres': 0, 'sucres': 0, 'sel': 0
        }
        
        for ing_rec in self.ingredients:
            ing_nutrition = ing_rec.ingredient.get_nutrition_for_quantity(ing_rec.quantite)
            for key in nutrition.keys():
                nutrition[key] += ing_nutrition[key]
        
        return {k: round(v, 1) for k, v in nutrition.items()}

    def calculer_disponibilite_ingredients(self) -> dict:
        """Calcule le pourcentage d'ingrédients disponibles dans le frigo."""
        if not self.ingredients:
            return {
                'pourcentage': 0,
                'ingredients_disponibles': [],
                'ingredients_manquants': [],
                'realisable': False,
                'score': 0
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
        
        return {
            'pourcentage': round(pourcentage, 1),
            'ingredients_disponibles': disponibles,
            'ingredients_manquants': manquants,
            'realisable': len(manquants) == 0,
            'score': len(disponibles)
        }

    # ============================================
    # ✅ NOUVELLE MÉTHODE : Score saisonnier
    # ============================================

    def calculer_score_saisonnier(self, saison: str = None) -> dict:
        """
        Calcule le score saisonnier de la recette.
        
        Args:
            saison: Saison de référence (défaut: saison actuelle)
        
        Returns:
            Dict avec score et détails des ingrédients
        """
        from utils.saisons import get_saison_actuelle
        
        if saison is None:
            saison = get_saison_actuelle()
        
        if not self.ingredients:
            return {
                'score': 0,
                'ingredients_saison': [],
                'ingredients_hors_saison': [],
                'ingredients_toute_annee': []
            }
        
        ingredients_saison = []
        ingredients_hors_saison = []
        ingredients_toute_annee = []
        
        for ing_rec in self.ingredients:
            ingredient = ing_rec.ingredient
            saisons_ing = ingredient.get_saisons()
            
            if not saisons_ing:
                ingredients_toute_annee.append(ingredient)
            elif saison in saisons_ing:
                ingredients_saison.append(ingredient)
            else:
                ingredients_hors_saison.append(ingredient)
        
        total = len(self.ingredients)
        positifs = len(ingredients_saison) + len(ingredients_toute_annee)
        score = round((positifs / total) * 100, 1) if total > 0 else 0
        
        return {
            'score': score,
            'ingredients_saison': ingredients_saison,
            'ingredients_hors_saison': ingredients_hors_saison,
            'ingredients_toute_annee': ingredients_toute_annee
        }

    def to_dict(self, include_ingredients=False, include_etapes=False, 
                include_nutrition=False, include_cout=False, 
                include_disponibilite=False, include_saison=False):
        """Convertit la recette en dictionnaire pour JSON"""
        data = {
            'id': self.id,
            'nom': self.nom,
            'instructions': self.instructions,
            'image': self.image,
            'type_recette': self.type_recette,
            'temps_preparation': self.temps_preparation
        }
        
        if include_ingredients:
            data['ingredients'] = [
                {
                    'ingredient_id': ing_rec.ingredient_id,
                    'ingredient_nom': ing_rec.ingredient.nom,
                    'quantite': ing_rec.quantite,
                    'unite': ing_rec.ingredient.unite,
                    'prix_unitaire': ing_rec.ingredient.prix_unitaire,
                    'poids_piece': ing_rec.ingredient.poids_piece,
                    'est_de_saison': ing_rec.ingredient.est_de_saison()
                }
                for ing_rec in self.ingredients
            ]
            data['nb_ingredients'] = len(self.ingredients)
        
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
        
        if include_nutrition:
            data['nutrition'] = self.calculer_nutrition()
        
        if include_cout:
            data['cout_estime'] = self.calculer_cout()
        
        if include_disponibilite:
            data['disponibilite'] = self.calculer_disponibilite_ingredients()
        
        # ✅ NOUVEAU : Score saisonnier
        if include_saison:
            data['saison'] = self.calculer_score_saisonnier()
        
        return data

    def __repr__(self):
        return f'<Recette {self.nom}>'


# ============================================
# ÉTAPES DE RECETTE
# ============================================

class EtapeRecette(db.Model):
    """Étapes de préparation d'une recette avec minuteurs optionnels"""
    id = db.Column(db.Integer, primary_key=True)
    recette_id = db.Column(db.Integer, db.ForeignKey('recette.id'), nullable=False)
    ordre = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text, nullable=False)
    duree_minutes = db.Column(db.Integer, nullable=True)
    
    def __repr__(self):
        return f'<EtapeRecette {self.recette_id} - Étape {self.ordre}>'


# ============================================
# LIAISON INGRÉDIENTS-RECETTES
# ============================================

class IngredientRecette(db.Model):
    """
    Table de liaison entre recettes et ingrédients.
    La quantité est stockée en UNITÉ NATIVE de l'ingrédient.
    """
    id = db.Column(db.Integer, primary_key=True)
    recette_id = db.Column(db.Integer, db.ForeignKey('recette.id'), nullable=False, index=True)
    ingredient_id = db.Column(db.Integer, db.ForeignKey('ingredient.id'), nullable=False, index=True)
    quantite = db.Column(db.Float, nullable=False)
    
    ingredient = db.relationship('Ingredient', backref='recettes')

    __table_args__ = (
        db.Index('idx_ing_recette_composite', 'recette_id', 'ingredient_id'),
    )
    
    def __repr__(self):
        return f'<IngredientRecette R:{self.recette_id} I:{self.ingredient_id}>'


# ============================================
# PLANIFICATION
# ============================================

class RecettePlanifiee(db.Model):
    """Modèle pour les recettes planifiées"""
    id = db.Column(db.Integer, primary_key=True)
    recette_id = db.Column(db.Integer, db.ForeignKey('recette.id', ondelete='CASCADE'), 
                          nullable=False, index=True)
    date_planification = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    date_preparation = db.Column(db.DateTime, nullable=True)
    preparee = db.Column(db.Boolean, default=False, index=True)

    __table_args__ = (
        db.Index('idx_planif_preparee_date', 'preparee', 'date_preparation'),
        db.Index('idx_planif_preparee_recette', 'preparee', 'recette_id'),
    )

    def to_dict(self, include_recette=False):
        """Convertit la recette planifiée en dictionnaire pour JSON"""
        data = {
            'id': self.id,
            'recette_id': self.recette_id,
            'recette_nom': self.recette_ref.nom,
            'date_planification': self.date_planification.isoformat(),
            'date_preparation': self.date_preparation.isoformat() if self.date_preparation else None,
            'preparee': self.preparee
        }
        
        if include_recette:
            data['recette'] = self.recette_ref.to_dict(
                include_ingredients=True,
                include_cout=True,
                include_saison=True
            )
        
        return data
    
    def __repr__(self):
        return f'<RecettePlanifiee {self.recette_id} - {self.date_planification}>'


# ============================================
# LISTE DE COURSES
# ============================================

class ListeCourses(db.Model):
    """Modèle pour la liste de courses - quantités en unités natives"""
    id = db.Column(db.Integer, primary_key=True)
    ingredient_id = db.Column(db.Integer, db.ForeignKey('ingredient.id'), nullable=False, index=True)
    quantite = db.Column(db.Float, nullable=False)
    achete = db.Column(db.Boolean, default=False, index=True)
    
    ingredient = db.relationship('Ingredient', backref='courses')

    __table_args__ = (
        db.Index('idx_courses_achete_ingredient', 'achete', 'ingredient_id'),
    )

    def to_dict(self, include_ingredient=False):
        """Convertit l'item de course en dictionnaire pour JSON"""
        data = {
            'id': self.id,
            'ingredient_id': self.ingredient_id,
            'ingredient_nom': self.ingredient.nom,
            'ingredient_unite': self.ingredient.unite,
            'quantite': self.quantite,
            'achete': self.achete,
            'est_de_saison': self.ingredient.est_de_saison()
        }
        
        if include_ingredient:
            data['ingredient'] = self.ingredient.to_dict(include_saisons=True)
        
        return data
    
    def __repr__(self):
        return f'<ListeCourses {self.ingredient_id}: {self.quantite}>'
