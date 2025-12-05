"""
Models pour le système de gestion des prix
"""
from datetime import datetime
from models.models import db


class PrixHistorique(db.Model):
    """
    Historique des prix collectés pour chaque ingrédient
    Permet de suivre l'évolution des prix dans le temps
    """
    __tablename__ = 'prix_historique'
    
    id = db.Column(db.Integer, primary_key=True)
    ingredient_id = db.Column(db.Integer, db.ForeignKey('ingredient.id'), nullable=False)
    prix = db.Column(db.Float, nullable=False)
    source = db.Column(db.String(50), nullable=False)  # 'openfoodfacts', 'carrefour', 'leclerc', 'manuel'
    url_source = db.Column(db.String(500), nullable=True)  # URL du produit source
    code_barre = db.Column(db.String(20), nullable=True)  # Code-barre EAN si disponible
    nom_produit = db.Column(db.String(200), nullable=True)  # Nom exact du produit trouvé
    quantite_reference = db.Column(db.Float, nullable=True)  # Quantité du produit (ex: 500g)
    unite_reference = db.Column(db.String(20), nullable=True)  # Unité (g, ml, unité)
    confiance = db.Column(db.Float, default=1.0)  # Score de confiance (0-1)
    date_collecte = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relations
    ingredient = db.relationship('Ingredient', backref='historique_prix')
    
    def __repr__(self):
        return f'<PrixHistorique {self.ingredient_id}: {self.prix}€ ({self.source})>'


class SourcePrix(db.Model):
    """
    Configuration des sources de prix
    Permet d'activer/désactiver des sources et de gérer leur priorité
    """
    __tablename__ = 'source_prix'
    
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(50), unique=True, nullable=False)
    actif = db.Column(db.Boolean, default=True)
    priorite = db.Column(db.Integer, default=50)  # Plus élevé = plus prioritaire
    fiabilite = db.Column(db.Float, default=0.8)  # Score de fiabilité (0-1)
    derniere_execution = db.Column(db.DateTime, nullable=True)
    erreurs_consecutives = db.Column(db.Integer, default=0)
    description = db.Column(db.Text, nullable=True)
    
    def __repr__(self):
        return f'<SourcePrix {self.nom} (priorité: {self.priorite})>'


class MappingIngredient(db.Model):
    """
    Mapping entre les noms d'ingrédients de la base et les produits trouvés
    Permet d'améliorer la précision des recherches au fil du temps
    """
    __tablename__ = 'mapping_ingredient'
    
    id = db.Column(db.Integer, primary_key=True)
    ingredient_id = db.Column(db.Integer, db.ForeignKey('ingredient.id'), nullable=False)
    terme_recherche = db.Column(db.String(200), nullable=False)
    source = db.Column(db.String(50), nullable=False)
    code_barre = db.Column(db.String(20), nullable=True)
    nom_produit_trouve = db.Column(db.String(200), nullable=True)
    validite_score = db.Column(db.Float, default=1.0)  # Score de validité du mapping
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    date_derniere_utilisation = db.Column(db.DateTime, default=datetime.utcnow)
    nombre_utilisations = db.Column(db.Integer, default=0)
    
    # Relations
    ingredient = db.relationship('Ingredient', backref='mappings')
    
    def __repr__(self):
        return f'<MappingIngredient {self.ingredient_id}: "{self.terme_recherche}">'
