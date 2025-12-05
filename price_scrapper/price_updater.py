#!/usr/bin/env python3
"""
Script de mise à jour périodique des prix
Peut être exécuté manuellement ou via cron
"""
import sys
import os
import argparse
import logging
from datetime import datetime
from typing import List, Optional

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models.models import db, Ingredient
from price_scraper.models import PrixHistorique, SourcePrix
from price_scraper.scrapers import OpenFoodFactsScraper
from price_scraper.config import ScraperConfig
from price_scraper.utils import (
    normaliser_nom_ingredient,
    obtenir_meilleur_mapping,
    sauvegarder_mapping,
    calculer_prix_moyen,
    detecter_anomalie_prix,
    nettoyer_historique,
    generer_rapport_prix
)


class PriceUpdater:
    """
    Gestionnaire principal de mise à jour des prix
    """
    
    def __init__(self, app):
        self.app = app
        self.config = ScraperConfig()
        self.logger = self._setup_logger()
        self.scrapers = {
            'openfoodfacts': OpenFoodFactsScraper()
        }
        self.stats = {
            'total_ingredients': 0,
            'mis_a_jour': 0,
            'erreurs': 0,
            'sautes': 0,
            'nouveaux_prix': 0
        }
    
    def _setup_logger(self) -> logging.Logger:
        """Configure le logger principal"""
        logger = logging.getLogger('price_updater')
        logger.setLevel(logging.INFO)
        
        # Handler fichier
        self.config.create_log_dir()
        fh = logging.FileHandler(f'{self.config.LOG_DIR}/price_updater.log')
        fh.setLevel(logging.INFO)
        
        # Handler console
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
    
    def initialiser_sources(self):
        """Initialise les sources de prix dans la base de données"""
        with self.app.app_context():
            for nom, config in self.config.SOURCES_CONFIG.items():
                source = SourcePrix.query.filter_by(nom=nom).first()
                if not source:
                    source = SourcePrix(
                        nom=nom,
                        actif=config['actif'],
                        priorite=config['priorite'],
                        fiabilite=config['fiabilite'],
                        description=config['description']
                    )
                    db.session.add(source)
            
            db.session.commit()
            self.logger.info("Sources de prix initialisées")
    
    def mettre_a_jour_tous_ingredients(self, forcer: bool = False,
                                       categorie: Optional[str] = None,
                                       limite: Optional[int] = None):
        """
        Met à jour les prix de tous les ingrédients
        
        Args:
            forcer: Forcer la mise à jour même si déjà à jour
            categorie: Filtrer par catégorie
            limite: Limiter le nombre d'ingrédients à traiter
        """
        with self.app.app_context():
            self.logger.info("=" * 60)
            self.logger.info("DÉBUT DE LA MISE À JOUR DES PRIX")
            self.logger.info("=" * 60)
            
            # Récupérer les ingrédients
            query = Ingredient.query
            if categorie:
                query = query.filter_by(categorie=categorie)
            if limite:
                query = query.limit(limite)
            
            ingredients = query.all()
            self.stats['total_ingredients'] = len(ingredients)
            
            self.logger.info(f"Nombre d'ingrédients à traiter: {len(ingredients)}")
            
            # Traiter chaque ingrédient
            for i, ingredient in enumerate(ingredients, 1):
                self.logger.info(f"\n[{i}/{len(ingredients)}] Traitement: {ingredient.nom}")
                
                try:
                    self.mettre_a_jour_ingredient(ingredient, forcer)
                except Exception as e:
                    self.logger.error(f"Erreur pour {ingredient.nom}: {e}")
                    self.stats['erreurs'] += 1
            
            # Générer le rapport final
            self._generer_rapport_final()
    
    def mettre_a_jour_ingredient(self, ingredient: Ingredient, forcer: bool = False):
        """
        Met à jour le prix d'un ingrédient spécifique
        
        Args:
            ingredient: Instance de l'ingrédient
            forcer: Forcer la mise à jour
        """
        # Vérifier si mise à jour nécessaire
        if not forcer and ingredient.prix_unitaire > 0:
            dernier_prix = PrixHistorique.query.filter_by(
                ingredient_id=ingredient.id
            ).order_by(PrixHistorique.date_collecte.desc()).first()
            
            if dernier_prix:
                jours_depuis = (datetime.utcnow() - dernier_prix.date_collecte).days
                if jours_depuis < 7:  # Pas de mise à jour si < 7 jours
                    self.logger.info(f"  ⏭️  Prix récent ({jours_depuis}j), sauté")
                    self.stats['sautes'] += 1
                    return
        
        # Normaliser le nom pour la recherche
        nom_recherche = normaliser_nom_ingredient(ingredient.nom)
        
        # Vérifier s'il existe un mapping
        mapping = obtenir_meilleur_mapping(ingredient.id, 'openfoodfacts')
        if mapping:
            nom_recherche = mapping.terme_recherche
            self.logger.info(f"  📋 Utilisation du mapping: {nom_recherche}")
        
        # Rechercher dans les scrapers actifs
        meilleurs_resultats = []
        
        for source_nom, scraper in self.scrapers.items():
            # Vérifier si la source est active
            source = SourcePrix.query.filter_by(nom=source_nom).first()
            if not source or not source.actif:
                continue
            
            try:
                self.logger.info(f"  🔍 Recherche dans {source_nom}...")
                resultats = scraper.rechercher_ingredient(
                    nom_recherche,
                    ingredient.categorie
                )
                
                if resultats:
                    self.logger.info(f"  ✓ {len(resultats)} résultats trouvés")
                    # Ajouter la source à chaque résultat
                    for r in resultats:
                        r['source'] = source_nom
                    meilleurs_resultats.extend(resultats[:3])  # Top 3 par source
                else:
                    self.logger.info(f"  ✗ Aucun résultat")
                
                # Mettre à jour la dernière exécution
                source.derniere_execution = datetime.utcnow()
                source.erreurs_consecutives = 0
                
            except Exception as e:
                self.logger.error(f"  ❌ Erreur avec {source_nom}: {e}")
                if source:
                    source.erreurs_consecutives += 1
        
        if not meilleurs_resultats:
            self.logger.warning(f"  ⚠️  Aucun prix trouvé pour {ingredient.nom}")
            return
        
        # Trier par confiance
        meilleurs_resultats.sort(key=lambda x: x['confiance'], reverse=True)
        meilleur = meilleurs_resultats[0]
        
        self.logger.info(f"  🏆 Meilleur résultat:")
        self.logger.info(f"      Produit: {meilleur['nom_produit']}")
        self.logger.info(f"      Prix: {meilleur['prix']}€/{meilleur['unite']}")
        self.logger.info(f"      Confiance: {meilleur['confiance']}")
        
        # Vérifier les anomalies
        anomalie = detecter_anomalie_prix(ingredient.id, meilleur['prix'])
        if anomalie['anomalie']:
            self.logger.warning(f"  ⚠️  Anomalie détectée: {anomalie['raison']}")
            # Réduire la confiance en cas d'anomalie
            meilleur['confiance'] *= 0.5
        
        # Sauvegarder dans l'historique
        prix_historique = PrixHistorique(
            ingredient_id=ingredient.id,
            prix=meilleur['prix'],
            source=meilleur['source'],
            url_source=meilleur.get('url'),
            code_barre=meilleur.get('code_barre'),
            nom_produit=meilleur['nom_produit'],
            quantite_reference=meilleur['quantite'],
            unite_reference=meilleur['unite'],
            confiance=meilleur['confiance']
        )
        db.session.add(prix_historique)
        self.stats['nouveaux_prix'] += 1
        
        # Mettre à jour le prix de l'ingrédient si confiance suffisante
        if meilleur['confiance'] >= self.config.CONFIANCE_MIN:
            ancien_prix = ingredient.prix_unitaire
            ingredient.prix_unitaire = meilleur['prix']
            
            if ancien_prix > 0:
                variation = ((meilleur['prix'] - ancien_prix) / ancien_prix) * 100
                self.logger.info(f"  💰 Prix mis à jour: {ancien_prix}€ → {meilleur['prix']}€ ({variation:+.1f}%)")
            else:
                self.logger.info(f"  💰 Nouveau prix: {meilleur['prix']}€")
            
            self.stats['mis_a_jour'] += 1
        else:
            self.logger.info(f"  ⚠️  Confiance trop faible ({meilleur['confiance']}), prix non mis à jour")
        
        # Sauvegarder le mapping si bon résultat
        if meilleur['confiance'] >= 0.7:
            sauvegarder_mapping(
                ingredient.id,
                nom_recherche,
                meilleur['source'],
                meilleur.get('code_barre'),
                meilleur['nom_produit'],
                meilleur['confiance']
            )
        
        db.session.commit()
    
    def _generer_rapport_final(self):
        """Génère et affiche le rapport final"""
        self.logger.info("\n" + "=" * 60)
        self.logger.info("RAPPORT FINAL")
        self.logger.info("=" * 60)
        self.logger.info(f"Ingrédients traités: {self.stats['total_ingredients']}")
        self.logger.info(f"Prix mis à jour: {self.stats['mis_a_jour']}")
        self.logger.info(f"Nouveaux prix collectés: {self.stats['nouveaux_prix']}")
        self.logger.info(f"Sautés (récents): {self.stats['sautes']}")
        self.logger.info(f"Erreurs: {self.stats['erreurs']}")
        
        # Statistiques globales
        rapport = generer_rapport_prix()
        self.logger.info(f"\nStatistiques globales:")
        self.logger.info(f"  Total prix en base: {rapport['total_prix']}")
        self.logger.info(f"  Prix récents (7j): {rapport['prix_recents_7j']}")
        self.logger.info(f"  Par source: {rapport['par_source']}")
        self.logger.info("=" * 60)


def main():
    """Point d'entrée principal"""
    parser = argparse.ArgumentParser(
        description='Mise à jour des prix des ingrédients'
    )
    parser.add_argument(
        '--forcer',
        action='store_true',
        help='Forcer la mise à jour même pour les prix récents'
    )
    parser.add_argument(
        '--categorie',
        type=str,
        help='Mettre à jour uniquement une catégorie'
    )
    parser.add_argument(
        '--limite',
        type=int,
        help='Limiter le nombre d\'ingrédients à traiter'
    )
    parser.add_argument(
        '--init-sources',
        action='store_true',
        help='Initialiser les sources de prix'
    )
    parser.add_argument(
        '--nettoyer',
        action='store_true',
        help='Nettoyer l\'historique ancien'
    )
    parser.add_argument(
        '--rapport',
        action='store_true',
        help='Générer uniquement un rapport'
    )
    
    args = parser.parse_args()
    
    # Créer l'application Flask
    app = create_app()
    updater = PriceUpdater(app)
    
    try:
        if args.init_sources:
            updater.initialiser_sources()
            print("✓ Sources initialisées")
        
        if args.nettoyer:
            with app.app_context():
                nettoyer_historique()
            print("✓ Historique nettoyé")
        
        if args.rapport:
            with app.app_context():
                rapport = generer_rapport_prix()
                print("\n📊 RAPPORT DES PRIX")
                print("=" * 50)
                print(f"Total prix: {rapport['total_prix']}")
                print(f"Prix récents (7j): {rapport['prix_recents_7j']}")
                print(f"Par source: {rapport['par_source']}")
                print("=" * 50)
        
        if not (args.init_sources or args.nettoyer or args.rapport):
            # Mise à jour normale
            updater.mettre_a_jour_tous_ingredients(
                forcer=args.forcer,
                categorie=args.categorie,
                limite=args.limite
            )
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Interruption utilisateur")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erreur fatale: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
