"""
Scraper pour Open Food Facts
Base de données collaborative de produits alimentaires
"""
from typing import Optional, Dict, List
import re
from price_scraper.scrapers.base_scraper import BaseScraper
from price_scraper.config import ScraperConfig


class OpenFoodFactsScraper(BaseScraper):
    """
    Scraper pour l'API Open Food Facts
    Documentation: https://wiki.openfoodfacts.org/API
    """
    
    def __init__(self):
        super().__init__('openfoodfacts')
        self.session.headers.update({
            'User-Agent': ScraperConfig.OPENFOODFACTS_USER_AGENT
        })
        self.api_url = ScraperConfig.OPENFOODFACTS_API_URL
        self.search_url = ScraperConfig.OPENFOODFACTS_SEARCH_URL
    
    def rechercher_ingredient(self, nom_ingredient: str, 
                             categorie: Optional[str] = None) -> List[Dict]:
        """
        Recherche un ingrédient dans Open Food Facts
        
        Args:
            nom_ingredient: Nom de l'ingrédient
            categorie: Catégorie (optionnel, peut améliorer les résultats)
        
        Returns:
            Liste de résultats avec prix estimés
        """
        self.logger.info(f"Recherche de '{nom_ingredient}' dans Open Food Facts")
        
        # Préparer les paramètres de recherche
        params = {
            'search_terms': nom_ingredient,
            'page_size': 20,
            'json': 1,
            'fields': 'code,product_name,quantity,brands,image_url,categories_tags'
        }
        
        # Ajouter la catégorie si fournie
        if categorie:
            category_tags = self._get_category_tags(categorie)
            if category_tags:
                params['tagtype_0'] = 'categories'
                params['tag_contains_0'] = 'contains'
                params['tag_0'] = category_tags[0]
        
        # Faire la requête
        response = self._make_request(self.search_url, params=params)
        
        if not response:
            self.logger.error("Impossible d'obtenir une réponse de Open Food Facts")
            return []
        
        try:
            data = response.json()
            products = data.get('products', [])
            
            self.logger.info(f"Trouvé {len(products)} produits")
            
            results = []
            for product in products:
                result = self._extraire_info_produit(product, nom_ingredient)
                if result:
                    results.append(result)
            
            # Trier par score de confiance décroissant
            results.sort(key=lambda x: x['confiance'], reverse=True)
            
            return results[:10]  # Retourner les 10 meilleurs résultats
            
        except Exception as e:
            self.logger.error(f"Erreur lors du parsing de la réponse: {e}")
            return []
    
    def obtenir_details_produit(self, code_barre: str) -> Optional[Dict]:
        """
        Obtient les détails d'un produit via son code-barre
        
        Args:
            code_barre: Code-barre EAN du produit
        
        Returns:
            Détails du produit ou None
        """
        self.logger.info(f"Récupération du produit avec code-barre {code_barre}")
        
        url = f"{self.api_url}/product/{code_barre}"
        response = self._make_request(url)
        
        if not response:
            return None
        
        try:
            data = response.json()
            if data.get('status') == 1:
                product = data.get('product', {})
                return self._extraire_info_produit(product, '')
            else:
                self.logger.warning(f"Produit {code_barre} non trouvé")
                return None
                
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération du produit: {e}")
            return None
    
    def _extraire_info_produit(self, product: Dict, 
                               nom_recherche: str) -> Optional[Dict]:
        """
        Extrait les informations pertinentes d'un produit Open Food Facts
        
        Args:
            product: Données du produit depuis l'API
            nom_recherche: Nom recherché (pour calculer le score de correspondance)
        
        Returns:
            Dictionnaire formaté ou None si données insuffisantes
        """
        try:
            # Informations de base
            nom_produit = product.get('product_name', '').strip()
            code_barre = product.get('code', '')
            
            if not nom_produit:
                return None
            
            # Quantité et unité
            quantity_str = product.get('quantity', '')
            quantite, unite = self._parse_quantite(quantity_str)
            
            if not quantite or not unite:
                self.logger.debug(f"Quantité invalide pour {nom_produit}: {quantity_str}")
                return None
            
            # Open Food Facts ne fournit pas directement les prix
            # On estime un prix moyen basé sur la catégorie et la quantité
            prix_estime = self._estimer_prix(product, quantite, unite)
            
            if prix_estime is None:
                return None
            
            # Normaliser le prix pour l'unité de base
            prix_normalise = self._normaliser_prix(prix_estime, quantite, unite, unite)
            
            if prix_normalise is None:
                return None
            
            # Score de correspondance du nom
            match_score = self._calculer_match_nom(nom_produit, nom_recherche)
            
            # Score de confiance
            has_barcode = bool(code_barre)
            has_image = bool(product.get('image_url'))
            confiance = self._calculer_score_confiance(match_score, has_barcode, has_image)
            
            # Note: Open Food Facts est plus utile pour les données nutritionnelles
            # que pour les prix, mais on peut l'utiliser comme estimation
            confiance *= 0.6  # Réduire la confiance car prix estimé
            
            return {
                'nom_produit': nom_produit,
                'prix': prix_normalise,
                'quantite': quantite,
                'unite': unite,
                'code_barre': code_barre if code_barre else None,
                'url': f"https://world.openfoodfacts.org/product/{code_barre}" if code_barre else None,
                'confiance': round(confiance, 2),
                'image_url': product.get('image_url'),
                'marque': product.get('brands', ''),
                'categories': product.get('categories_tags', [])
            }
            
        except Exception as e:
            self.logger.error(f"Erreur extraction produit: {e}")
            return None
    
    def _parse_quantite(self, quantity_str: str) -> tuple[Optional[float], Optional[str]]:
        """
        Parse une chaîne de quantité (ex: "500g", "1L", "250 ml")
        
        Returns:
            Tuple (quantite, unite) ou (None, None) si parsing échoue
        """
        if not quantity_str:
            return None, None
        
        # Nettoyer la chaîne
        quantity_str = quantity_str.lower().strip()
        
        # Patterns de reconnaissance
        patterns = [
            (r'(\d+(?:[.,]\d+)?)\s*kg', 'kg'),
            (r'(\d+(?:[.,]\d+)?)\s*g', 'g'),
            (r'(\d+(?:[.,]\d+)?)\s*l', 'l'),
            (r'(\d+(?:[.,]\d+)?)\s*ml', 'ml'),
            (r'(\d+(?:[.,]\d+)?)\s*cl', 'cl'),
        ]
        
        for pattern, unite in patterns:
            match = re.search(pattern, quantity_str)
            if match:
                try:
                    quantite = float(match.group(1).replace(',', '.'))
                    return quantite, unite
                except ValueError:
                    continue
        
        return None, None
    
    def _estimer_prix(self, product: Dict, quantite: float, 
                     unite: str) -> Optional[float]:
        """
        Estime un prix pour un produit basé sur sa catégorie et sa quantité
        
        Note: Open Food Facts ne contient généralement pas de prix.
        Cette fonction fournit une estimation très approximative.
        Pour des prix réels, il faudrait utiliser des scrapers de supermarchés.
        """
        # Prix moyens estimés par kg/L (valeurs approximatives France 2024)
        prix_moyens = {
            'vegetables': 3.0,  # légumes
            'fruits': 4.0,
            'meat': 15.0,
            'fish': 18.0,
            'dairy': 5.0,
            'cheese': 12.0,
            'pasta': 2.5,
            'rice': 2.0,
            'bread': 4.0,
            'beverages': 2.0,
            'default': 5.0
        }
        
        # Identifier la catégorie
        categories = product.get('categories_tags', [])
        prix_kg = prix_moyens['default']
        
        for cat in categories:
            for key, prix in prix_moyens.items():
                if key in cat:
                    prix_kg = prix
                    break
        
        # Convertir la quantité en kg/L
        quantite_base = quantite
        if unite == 'g':
            quantite_base = quantite / 1000
        elif unite == 'ml' or unite == 'cl':
            quantite_base = quantite / 1000 if unite == 'ml' else quantite / 100
        
        prix_estime = prix_kg * quantite_base
        
        return round(prix_estime, 2) if prix_estime > 0 else None
    
    def _calculer_match_nom(self, nom_produit: str, nom_recherche: str) -> float:
        """
        Calcule un score de correspondance entre le nom du produit et la recherche
        
        Returns:
            Score entre 0 et 1
        """
        if not nom_recherche:
            return 0.8  # Score par défaut si pas de recherche
        
        nom_produit = nom_produit.lower()
        nom_recherche = nom_recherche.lower()
        
        # Mots de la recherche
        mots_recherche = set(nom_recherche.split())
        mots_produit = set(nom_produit.split())
        
        # Correspondance exacte
        if nom_recherche in nom_produit:
            return 1.0
        
        # Nombre de mots en commun
        mots_communs = mots_recherche & mots_produit
        if not mots_recherche:
            return 0.5
        
        score = len(mots_communs) / len(mots_recherche)
        
        return min(score, 1.0)
    
    def _get_category_tags(self, categorie: str) -> List[str]:
        """
        Convertit une catégorie en tags Open Food Facts
        """
        mapping = ScraperConfig.CATEGORIES_MAPPING.get(categorie, [])
        return mapping
