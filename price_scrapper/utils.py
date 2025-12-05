"""
Utilitaires pour la gestion des prix
"""
from typing import Optional, List, Dict
from datetime import datetime, timedelta
from models.models import Ingredient
from price_scraper.models import PrixHistorique, MappingIngredient
from price_scraper.config import ScraperConfig
import logging

logger = logging.getLogger('price_utils')


def normaliser_nom_ingredient(nom: str) -> str:
    """
    Normalise un nom d'ingrédient pour la recherche
    
    Args:
        nom: Nom de l'ingrédient
    
    Returns:
        Nom normalisé
    """
    # Mettre en minuscules
    nom = nom.lower().strip()
    
    # Supprimer les articles
    articles = ['le ', 'la ', 'les ', 'un ', 'une ', 'des ', 'du ', 'de la ']
    for article in articles:
        if nom.startswith(article):
            nom = nom[len(article):]
    
    # Supprimer les parenthèses et leur contenu
    import re
    nom = re.sub(r'\([^)]*\)', '', nom).strip()
    
    return nom


def obtenir_meilleur_mapping(ingredient_id: int, source: str) -> Optional[MappingIngredient]:
    """
    Obtient le meilleur mapping pour un ingrédient et une source
    
    Args:
        ingredient_id: ID de l'ingrédient
        source: Nom de la source
    
    Returns:
        Meilleur mapping ou None
    """
    from models.models import db
    
    mappings = MappingIngredient.query.filter_by(
        ingredient_id=ingredient_id,
        source=source
    ).order_by(
        MappingIngredient.validite_score.desc(),
        MappingIngredient.nombre_utilisations.desc()
    ).all()
    
    if mappings:
        # Mettre à jour le mapping utilisé
        mapping = mappings[0]
        mapping.nombre_utilisations += 1
        mapping.date_derniere_utilisation = datetime.utcnow()
        db.session.commit()
        return mapping
    
    return None


def sauvegarder_mapping(ingredient_id: int, terme_recherche: str, source: str,
                       code_barre: Optional[str] = None,
                       nom_produit: Optional[str] = None,
                       validite_score: float = 1.0):
    """
    Sauvegarde un nouveau mapping ou met à jour un existant
    
    Args:
        ingredient_id: ID de l'ingrédient
        terme_recherche: Terme de recherche utilisé
        source: Source du mapping
        code_barre: Code-barre du produit (optionnel)
        nom_produit: Nom du produit trouvé (optionnel)
        validite_score: Score de validité du mapping
    """
    from models.models import db
    
    # Chercher un mapping existant
    mapping = MappingIngredient.query.filter_by(
        ingredient_id=ingredient_id,
        terme_recherche=terme_recherche,
        source=source
    ).first()
    
    if mapping:
        # Mettre à jour
        mapping.validite_score = validite_score
        mapping.nombre_utilisations += 1
        mapping.date_derniere_utilisation = datetime.utcnow()
        if code_barre:
            mapping.code_barre = code_barre
        if nom_produit:
            mapping.nom_produit_trouve = nom_produit
    else:
        # Créer nouveau
        mapping = MappingIngredient(
            ingredient_id=ingredient_id,
            terme_recherche=terme_recherche,
            source=source,
            code_barre=code_barre,
            nom_produit_trouve=nom_produit,
            validite_score=validite_score
        )
        db.session.add(mapping)
    
    db.session.commit()
    logger.info(f"Mapping sauvegardé: {terme_recherche} -> {nom_produit}")


def calculer_prix_moyen(ingredient_id: int, jours: int = 30,
                       sources: Optional[List[str]] = None,
                       confiance_min: float = 0.5) -> Optional[float]:
    """
    Calcule le prix moyen d'un ingrédient sur une période
    
    Args:
        ingredient_id: ID de l'ingrédient
        jours: Nombre de jours à considérer
        sources: Liste des sources à considérer (None = toutes)
        confiance_min: Score de confiance minimum
    
    Returns:
        Prix moyen ou None
    """
    date_limite = datetime.utcnow() - timedelta(days=jours)
    
    query = PrixHistorique.query.filter(
        PrixHistorique.ingredient_id == ingredient_id,
        PrixHistorique.date_collecte >= date_limite,
        PrixHistorique.confiance >= confiance_min
    )
    
    if sources:
        query = query.filter(PrixHistorique.source.in_(sources))
    
    prix_list = query.all()
    
    if not prix_list:
        return None
    
    # Calculer la moyenne pondérée par la confiance
    total_prix = 0
    total_poids = 0
    
    for prix in prix_list:
        poids = prix.confiance
        total_prix += prix.prix * poids
        total_poids += poids
    
    if total_poids > 0:
        return round(total_prix / total_poids, 2)
    
    return None


def detecter_anomalie_prix(ingredient_id: int, nouveau_prix: float,
                          seuil_hausse: Optional[float] = None,
                          seuil_baisse: Optional[float] = None) -> Dict:
    """
    Détecte si un nouveau prix est anormal par rapport à l'historique
    
    Args:
        ingredient_id: ID de l'ingrédient
        nouveau_prix: Nouveau prix à vérifier
        seuil_hausse: Seuil de hausse max (défaut: config)
        seuil_baisse: Seuil de baisse max (défaut: config)
    
    Returns:
        Dictionnaire avec 'anomalie' (bool) et 'raison' (str)
    """
    config = ScraperConfig()
    
    if seuil_hausse is None:
        seuil_hausse = config.VARIATION_MAX_HAUSSE
    if seuil_baisse is None:
        seuil_baisse = config.VARIATION_MAX_BAISSE
    
    # Obtenir le prix moyen récent
    prix_moyen = calculer_prix_moyen(ingredient_id, jours=30)
    
    if prix_moyen is None:
        # Pas d'historique, vérifier les limites absolues
        if nouveau_prix < config.PRIX_MIN:
            return {
                'anomalie': True,
                'raison': f'Prix trop bas: {nouveau_prix}€ < {config.PRIX_MIN}€'
            }
        if nouveau_prix > config.PRIX_MAX:
            return {
                'anomalie': True,
                'raison': f'Prix trop élevé: {nouveau_prix}€ > {config.PRIX_MAX}€'
            }
        return {'anomalie': False, 'raison': 'Pas d\'historique'}
    
    # Calculer la variation
    variation = nouveau_prix / prix_moyen
    
    if variation > seuil_hausse:
        return {
            'anomalie': True,
            'raison': f'Hausse excessive: {variation:.1%} (moyen: {prix_moyen}€)'
        }
    
    if variation < seuil_baisse:
        return {
            'anomalie': True,
            'raison': f'Baisse excessive: {variation:.1%} (moyen: {prix_moyen}€)'
        }
    
    return {'anomalie': False, 'raison': 'Prix normal'}


def nettoyer_historique(jours_retention: int = 180):
    """
    Nettoie l'historique des prix en gardant uniquement les données récentes
    et les données statistiquement importantes
    
    Args:
        jours_retention: Nombre de jours à conserver
    """
    from models.models import db
    
    date_limite = datetime.utcnow() - timedelta(days=jours_retention)
    
    # Supprimer les anciens prix avec faible confiance
    deleted = PrixHistorique.query.filter(
        PrixHistorique.date_collecte < date_limite,
        PrixHistorique.confiance < 0.7
    ).delete()
    
    db.session.commit()
    logger.info(f"{deleted} entrées d'historique supprimées")


def generer_rapport_prix(ingredient_id: Optional[int] = None) -> Dict:
    """
    Génère un rapport sur les prix collectés
    
    Args:
        ingredient_id: ID d'un ingrédient spécifique (None = tous)
    
    Returns:
        Dictionnaire avec les statistiques
    """
    from models.models import db
    
    query = PrixHistorique.query
    if ingredient_id:
        query = query.filter_by(ingredient_id=ingredient_id)
    
    total_prix = query.count()
    
    # Prix par source
    sources = db.session.query(
        PrixHistorique.source,
        db.func.count(PrixHistorique.id).label('count')
    ).group_by(PrixHistorique.source).all()
    
    # Prix récents (7 derniers jours)
    date_limite = datetime.utcnow() - timedelta(days=7)
    recents = query.filter(PrixHistorique.date_collecte >= date_limite).count()
    
    return {
        'total_prix': total_prix,
        'prix_recents_7j': recents,
        'par_source': {source: count for source, count in sources},
        'date_generation': datetime.utcnow().isoformat()
    }
