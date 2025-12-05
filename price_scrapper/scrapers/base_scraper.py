"""
Classe de base pour tous les scrapers de prix
"""
import time
import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, List
import requests
from price_scraper.config import ScraperConfig


class BaseScraper(ABC):
    """
    Classe abstraite de base pour tous les scrapers
    """
    
    def __init__(self, source_name: str):
        self.source_name = source_name
        self.config = ScraperConfig()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.config.USER_AGENT
        })
        self.logger = self._setup_logger()
        self.last_request_time = 0
        
    def _setup_logger(self) -> logging.Logger:
        """Configure le logger pour ce scraper"""
        logger = logging.getLogger(f'scraper.{self.source_name}')
        logger.setLevel(logging.INFO)
        
        # Handler pour fichier
        self.config.create_log_dir()
        fh = logging.FileHandler(
            f'{self.config.LOG_DIR}/scraper_{self.source_name}.log'
        )
        fh.setLevel(logging.INFO)
        
        # Handler pour console
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        
        # Format
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        
        logger.addHandler(fh)
        logger.addHandler(ch)
        
        return logger
    
    def _respect_rate_limit(self):
        """Respecte les limites de taux de requêtes"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.config.REQUEST_DELAY:
            time.sleep(self.config.REQUEST_DELAY - elapsed)
        self.last_request_time = time.time()
    
    def _make_request(self, url: str, params: Optional[Dict] = None, 
                      method: str = 'GET') -> Optional[requests.Response]:
        """
        Effectue une requête HTTP avec gestion des erreurs et retry
        """
        self._respect_rate_limit()
        
        for attempt in range(self.config.MAX_RETRIES):
            try:
                if method == 'GET':
                    response = self.session.get(
                        url,
                        params=params,
                        timeout=self.config.REQUEST_TIMEOUT
                    )
                elif method == 'POST':
                    response = self.session.post(
                        url,
                        json=params,
                        timeout=self.config.REQUEST_TIMEOUT
                    )
                else:
                    raise ValueError(f"Méthode HTTP non supportée: {method}")
                
                response.raise_for_status()
                return response
                
            except requests.exceptions.RequestException as e:
                self.logger.warning(
                    f"Tentative {attempt + 1}/{self.config.MAX_RETRIES} échouée: {e}"
                )
                if attempt < self.config.MAX_RETRIES - 1:
                    time.sleep(self.config.RETRY_DELAY * (attempt + 1))
                else:
                    self.logger.error(f"Échec de la requête après {self.config.MAX_RETRIES} tentatives")
                    return None
        
        return None
    
    def _normaliser_prix(self, prix: float, quantite: float, 
                        unite_source: str, unite_cible: str) -> Optional[float]:
        """
        Normalise un prix pour une unité cible
        
        Args:
            prix: Prix du produit
            quantite: Quantité du produit
            unite_source: Unité de la quantité source
            unite_cible: Unité cible pour le prix
        
        Returns:
            Prix normalisé pour l'unité cible, ou None si conversion impossible
        """
        try:
            # Normaliser les unités en minuscules
            unite_source = unite_source.lower().strip()
            unite_cible = unite_cible.lower().strip()
            
            # Si les unités sont identiques
            if unite_source == unite_cible:
                return prix / quantite if quantite > 0 else None
            
            # Trouver le facteur de conversion
            facteur = None
            for unite_base, conversions in self.config.UNITES_CONVERSION.items():
                if unite_source in conversions and unite_cible in conversions:
                    facteur = conversions[unite_cible] / conversions[unite_source]
                    break
            
            if facteur is None:
                self.logger.warning(
                    f"Conversion impossible: {unite_source} -> {unite_cible}"
                )
                return None
            
            # Calculer le prix normalisé
            prix_unitaire = prix / quantite if quantite > 0 else None
            if prix_unitaire is None:
                return None
            
            prix_normalise = prix_unitaire / facteur
            
            # Vérifier que le prix est dans une plage acceptable
            if self.config.PRIX_MIN <= prix_normalise <= self.config.PRIX_MAX:
                return round(prix_normalise, 2)
            else:
                self.logger.warning(
                    f"Prix normalisé hors limites: {prix_normalise}€"
                )
                return None
                
        except Exception as e:
            self.logger.error(f"Erreur lors de la normalisation du prix: {e}")
            return None
    
    def _calculer_score_confiance(self, match_nom: float, 
                                   has_barcode: bool,
                                   has_image: bool) -> float:
        """
        Calcule un score de confiance pour un résultat
        
        Args:
            match_nom: Score de correspondance du nom (0-1)
            has_barcode: Le produit a un code-barre
            has_image: Le produit a une image
        
        Returns:
            Score de confiance entre 0 et 1
        """
        score = match_nom * 0.6  # 60% basé sur le nom
        if has_barcode:
            score += 0.3  # +30% si code-barre
        if has_image:
            score += 0.1  # +10% si image
        
        return min(score, 1.0)
    
    @abstractmethod
    def rechercher_ingredient(self, nom_ingredient: str, 
                             categorie: Optional[str] = None) -> List[Dict]:
        """
        Recherche un ingrédient et retourne les résultats
        
        Args:
            nom_ingredient: Nom de l'ingrédient à rechercher
            categorie: Catégorie de l'ingrédient (optionnel)
        
        Returns:
            Liste de dictionnaires contenant les informations de prix
            Format attendu:
            {
                'nom_produit': str,
                'prix': float,
                'quantite': float,
                'unite': str,
                'code_barre': Optional[str],
                'url': Optional[str],
                'confiance': float,
                'image_url': Optional[str]
            }
        """
        pass
    
    @abstractmethod
    def obtenir_details_produit(self, code_barre: str) -> Optional[Dict]:
        """
        Obtient les détails d'un produit à partir de son code-barre
        
        Args:
            code_barre: Code-barre du produit
        
        Returns:
            Dictionnaire avec les détails du produit, ou None si non trouvé
        """
        pass
