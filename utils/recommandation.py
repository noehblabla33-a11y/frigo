from typing import List, Dict, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from functools import lru_cache


@dataclass
class CritereRecommandation:
    """
    Définition d'un critère de recommandation.

    Attributes:
        nom: Identifiant unique du critère
        poids: Pondération du critère (0.0 à 1.0, défaut: 1.0)
        actif: Si le critère est pris en compte
        description: Description pour l'interface utilisateur
        emoji: Emoji pour l'affichage
    """
    nom: str
    poids: float = 1.0
    actif: bool = True
    description: str = ""
    emoji: str = "📊"

    def __post_init__(self):
        self.poids = max(0.0, min(1.0, self.poids))


@dataclass
class ScoreRecette:
    """
    Score d'une recette avec détail par critère.

    Attributes:
        recette: L'objet Recette
        score_total: Score final pondéré (0-100)
        scores_details: Scores individuels par critère
        meta: Métadonnées additionnelles pour l'affichage
    """
    recette: object
    score_total: float = 0.0
    scores_details: Dict[str, float] = field(default_factory=dict)
    meta: Dict[str, any] = field(default_factory=dict)


def score_saison(recette, saison: str = None) -> tuple[float, dict]:
    """
    Calcule le score saisonnier d'une recette.

    Returns:
        Tuple (score 0-100, métadonnées)
    """
    saison_info = recette.calculer_score_saisonnier(saison)
    return saison_info['score'], {
        'ingredients_saison': len(saison_info['ingredients_saison']),
        'ingredients_hors_saison': len(saison_info['ingredients_hors_saison']),
        'ingredients_toute_annee': len(saison_info['ingredients_toute_annee'])
    }


def score_disponibilite(recette) -> tuple[float, dict]:
    """
    Calcule le score de disponibilité des ingrédients.

    Returns:
        Tuple (score 0-100, métadonnées)
    """
    dispo = recette.calculer_disponibilite_ingredients()
    return dispo['pourcentage'], {
        'realisable': dispo['realisable'],
        'nb_disponibles': len(dispo['ingredients_disponibles']),
        'nb_manquants': len(dispo['ingredients_manquants'])
    }


def score_cout(recette, cout_max: float = None) -> tuple[float, dict]:
    """
    Calcule le score de coût (inversé : moins cher = meilleur score).

    Args:
        cout_max: Coût maximum de référence pour normalisation

    Returns:
        Tuple (score 0-100, métadonnées)
    """
    cout = recette.calculer_cout()

    if cout <= 0:
        return 50.0, {'cout': 0, 'cout_max': cout_max, 'sans_prix': True}

    if cout_max is None or cout_max <= 0:
        cout_max = 50.0

    score = max(0, 100 * (1 - cout / cout_max))

    return round(score, 1), {'cout': cout, 'cout_max': cout_max, 'sans_prix': False}


def score_temps(recette, temps_max: int = 120) -> tuple:
    """
    Score basé sur le temps total de préparation (préparation + cuisson).

    Plus c'est rapide, meilleur est le score.

    Args:
        recette: Instance de Recette
        temps_max: Temps maximum attendu en minutes (pour normalisation)

    Returns:
        Tuple (score 0-100, métadonnées)
    """
    temps_total = recette.temps_total()

    if temps_total is None or temps_total <= 0:
        return 80.0, {
            'temps_total': None,
            'temps_preparation': recette.temps_preparation,
            'temps_cuisson': recette.temps_cuisson
        }

    if temps_total >= temps_max:
        score = 20.0
    else:
        score = 100 - (temps_total / temps_max * 80)

    return round(score, 1), {
        'temps_total': temps_total,
        'temps_preparation': recette.temps_preparation,
        'temps_cuisson': recette.temps_cuisson
    }


def score_nutrition_equilibre(recette) -> tuple[float, dict]:
    """
    Calcule un score d'équilibre nutritionnel basé sur les macronutriments.

    Cibles : protéines 15-25%, glucides 45-55%, lipides 25-35% des calories.

    Returns:
        Tuple (score 0-100, métadonnées)
    """
    nutrition = recette.calculer_nutrition()
    calories = nutrition.get('calories', 0)

    if calories <= 0:
        return 50.0, {'sans_nutrition': True}

    cal_prot = nutrition.get('proteines', 0) * 4
    cal_gluc = nutrition.get('glucides', 0) * 4
    cal_lip = nutrition.get('lipides', 0) * 9

    total_cal_macros = cal_prot + cal_gluc + cal_lip
    if total_cal_macros <= 0:
        return 50.0, {'sans_nutrition': True}

    pct_prot = (cal_prot / total_cal_macros) * 100
    pct_gluc = (cal_gluc / total_cal_macros) * 100
    pct_lip = (cal_lip / total_cal_macros) * 100

    cible_prot, plage_prot = 20, 10
    cible_gluc, plage_gluc = 50, 10
    cible_lip, plage_lip = 30, 10

    def score_macro(pct: float, cible: float, plage: float) -> float:
        ecart = abs(pct - cible)
        if ecart <= plage:
            return 100.0
        return max(0, 100 - (ecart - plage) * 5)

    score_p = score_macro(pct_prot, cible_prot, plage_prot)
    score_g = score_macro(pct_gluc, cible_gluc, plage_gluc)
    score_l = score_macro(pct_lip, cible_lip, plage_lip)

    score = (score_p + score_g + score_l) / 3

    return round(score, 1), {
        'sans_nutrition': False,
        'pct_proteines': round(pct_prot, 1),
        'pct_glucides': round(pct_gluc, 1),
        'pct_lipides': round(pct_lip, 1),
        'calories': calories
    }


def score_variete(recette, historique_recettes: List[int] = None,
                  jours_penalite: int = 14) -> tuple[float, dict]:
    """
    Calcule un score de variété (pénalise les recettes récemment cuisinées).

    Args:
        historique_recettes: Liste des IDs de recettes cuisinées récemment
                            (ordonnées de la plus récente à la plus ancienne)
        jours_penalite: Nombre de jours de pénalité

    Returns:
        Tuple (score 0-100, métadonnées)
    """
    if not historique_recettes:
        return 100.0, {'dans_historique': False, 'position': None}

    recette_id = recette.id

    if recette_id not in historique_recettes:
        return 100.0, {'dans_historique': False, 'position': None}

    position = historique_recettes.index(recette_id)
    nb_recettes = len(historique_recettes)

    score = 20 + (position / max(1, nb_recettes - 1)) * 70

    return round(score, 1), {'dans_historique': True, 'position': position + 1}


class MoteurRecommandation:
    """
    Moteur de recommandation de recettes avec critères pondérables.
    """

    CRITERES_DISPONIBLES = {
        'saison': {
            'description': 'Ingrédients de saison',
            'emoji': '🌿',
            'calculateur': score_saison,
            'poids_defaut': 0.7
        },
        'disponibilite': {
            'description': 'Ingrédients en stock',
            'emoji': '❄️',
            'calculateur': score_disponibilite,
            'poids_defaut': 1.0
        },
        'cout': {
            'description': 'Coût de la recette',
            'emoji': '💰',
            'calculateur': score_cout,
            'poids_defaut': 0.5
        },
        'temps': {
            'description': 'Temps de préparation',
            'emoji': '⏱️',
            'calculateur': score_temps,
            'poids_defaut': 0.4
        },
        'nutrition': {
            'description': 'Équilibre nutritionnel',
            'emoji': '🥗',
            'calculateur': score_nutrition_equilibre,
            'poids_defaut': 0.3
        },
        'variete': {
            'description': 'Variété des repas',
            'emoji': '🔄',
            'calculateur': score_variete,
            'poids_defaut': 0.6
        }
    }

    def __init__(self):
        """Initialise le moteur avec les critères par défaut."""
        self.criteres: Dict[str, CritereRecommandation] = {}
        self.contexte: Dict[str, any] = {}

        for nom, config in self.CRITERES_DISPONIBLES.items():
            self.criteres[nom] = CritereRecommandation(
                nom=nom,
                poids=config['poids_defaut'],
                actif=True,
                description=config['description'],
                emoji=config['emoji']
            )

    def configurer_critere(self, nom: str, poids: float = None, actif: bool = None) -> 'MoteurRecommandation':
        """
        Configure un critère de recommandation.

        Args:
            nom: Nom du critère
            poids: Nouvelle pondération (0.0 à 1.0)
            actif: Activer/désactiver le critère

        Returns:
            self pour chaînage
        """
        if nom not in self.criteres:
            raise ValueError(f"Critère inconnu: {nom}. Disponibles: {list(self.criteres.keys())}")

        if poids is not None:
            self.criteres[nom].poids = max(0.0, min(1.0, poids))

        if actif is not None:
            self.criteres[nom].actif = actif

        return self

    def configurer_criteres(self, config: Dict[str, float]) -> 'MoteurRecommandation':
        """
        Configure plusieurs critères en une fois.

        Args:
            config: Dictionnaire {nom_critere: poids}

        Returns:
            self pour chaînage
        """
        for nom, poids in config.items():
            self.configurer_critere(nom, poids=poids)
        return self

    def desactiver_critere(self, nom: str) -> 'MoteurRecommandation':
        """Désactive un critère."""
        return self.configurer_critere(nom, actif=False)

    def activer_critere(self, nom: str) -> 'MoteurRecommandation':
        """Active un critère."""
        return self.configurer_critere(nom, actif=True)

    def set_contexte(self, **kwargs) -> 'MoteurRecommandation':
        """
        Définit le contexte pour les calculs.

        Args:
            saison: Saison de référence (défaut: saison actuelle)
            cout_max: Coût maximum pour normalisation
            temps_max: Temps maximum pour normalisation
            historique_recettes: Liste des IDs de recettes récentes

        Returns:
            self pour chaînage
        """
        self.contexte.update(kwargs)
        return self

    def _calculer_score_recette(self, recette) -> ScoreRecette:
        """
        Calcule le score total d'une recette.

        Returns:
            ScoreRecette avec tous les détails
        """
        result = ScoreRecette(recette=recette)
        somme_ponderee = 0.0
        somme_poids = 0.0

        for nom, critere in self.criteres.items():
            if not critere.actif or critere.poids <= 0:
                continue

            config = self.CRITERES_DISPONIBLES[nom]
            calculateur = config['calculateur']

            try:
                if nom == 'saison':
                    score, meta = calculateur(recette, self.contexte.get('saison'))
                elif nom == 'cout':
                    score, meta = calculateur(recette, self.contexte.get('cout_max'))
                elif nom == 'temps':
                    score, meta = calculateur(recette, self.contexte.get('temps_max'))
                elif nom == 'variete':
                    score, meta = calculateur(
                        recette,
                        self.contexte.get('historique_recettes', [])
                    )
                else:
                    score, meta = calculateur(recette)

                result.scores_details[nom] = score
                result.meta[nom] = meta

                somme_ponderee += score * critere.poids
                somme_poids += critere.poids

            except Exception as e:
                result.scores_details[nom] = 50.0
                result.meta[nom] = {'erreur': str(e)}
                somme_ponderee += 50.0 * critere.poids
                somme_poids += critere.poids

        if somme_poids > 0:
            result.score_total = round(somme_ponderee / somme_poids, 1)
        else:
            result.score_total = 0.0

        return result

    def recommander(self, recettes, limit: int = None,
                    filtre_realisable: bool = False,
                    filtre_type: str = None,
                    score_minimum: float = None) -> List[ScoreRecette]:
        """
        Génère les recommandations triées par score.

        Args:
            recettes: Liste ou Query de recettes
            limit: Nombre maximum de résultats
            filtre_realisable: Ne garder que les recettes réalisables
            filtre_type: Filtrer par type de recette
            score_minimum: Score minimum pour être inclus

        Returns:
            Liste de ScoreRecette triée par score décroissant
        """
        resultats = []

        for recette in recettes:
            if filtre_type and recette.type_recette != filtre_type:
                continue

            score_recette = self._calculer_score_recette(recette)

            if filtre_realisable:
                dispo = score_recette.meta.get('disponibilite', {})
                if not dispo.get('realisable', False):
                    continue

            if score_minimum is not None and score_recette.score_total < score_minimum:
                continue

            resultats.append(score_recette)

        resultats.sort(key=lambda x: x.score_total, reverse=True)

        if limit:
            resultats = resultats[:limit]

        return resultats

    def get_criteres_actifs(self) -> List[CritereRecommandation]:
        """Retourne la liste des critères actifs."""
        return [c for c in self.criteres.values() if c.actif and c.poids > 0]

    def get_config(self) -> Dict[str, Dict]:
        """
        Retourne la configuration actuelle pour affichage/persistance.

        Returns:
            Dict avec la config de chaque critère
        """
        return {
            nom: {
                'poids': c.poids,
                'actif': c.actif,
                'description': c.description,
                'emoji': c.emoji
            }
            for nom, c in self.criteres.items()
        }


def get_historique_recettes_ids(jours: int = 14) -> List[int]:
    """
    Récupère les IDs des recettes cuisinées récemment.

    Args:
        jours: Nombre de jours à considérer

    Returns:
        Liste d'IDs ordonnée de la plus récente à la plus ancienne
    """
    from models.models import RecettePlanifiee

    date_limite = datetime.utcnow() - timedelta(days=jours)

    recettes = RecettePlanifiee.query\
        .filter(RecettePlanifiee.preparee == True)\
        .filter(RecettePlanifiee.date_preparation >= date_limite)\
        .order_by(RecettePlanifiee.date_preparation.desc())\
        .all()

    return [r.recette_id for r in recettes]


def get_cout_max_recettes() -> float:
    """
    Calcule le coût maximum parmi toutes les recettes.

    Returns:
        Coût maximum ou 50.0 par défaut
    """
    from models.models import Recette

    recettes = Recette.query.all()
    if not recettes:
        return 50.0

    couts = [r.calculer_cout() for r in recettes]
    couts = [c for c in couts if c > 0]

    return max(couts) if couts else 50.0


def get_temps_max_recettes() -> int:
    """
    Calcule le temps maximum parmi toutes les recettes.

    Returns:
        Temps maximum en minutes ou 120 par défaut
    """
    from models.models import Recette

    temps = Recette.query\
        .with_entities(Recette.temps_preparation)\
        .filter(Recette.temps_preparation.isnot(None))\
        .filter(Recette.temps_preparation > 0)\
        .all()

    temps_values = [t[0] for t in temps]

    return max(temps_values) if temps_values else 120


def creer_moteur_recommandation_standard(saison: str = None) -> MoteurRecommandation:
    """
    Crée un moteur de recommandation avec une configuration standard.

    Args:
        saison: Saison à utiliser (défaut: saison actuelle)

    Returns:
        MoteurRecommandation configuré
    """
    from utils.saisons import get_saison_actuelle

    moteur = MoteurRecommandation()

    moteur.set_contexte(
        saison=saison or get_saison_actuelle(),
        cout_max=get_cout_max_recettes(),
        temps_max=get_temps_max_recettes(),
        historique_recettes=get_historique_recettes_ids(14)
    )

    return moteur


def recommander_recettes_saison(limit: int = 10,
                                 filtre_realisable: bool = False) -> List[ScoreRecette]:
    """
    Obtient des recommandations basées sur la saison actuelle.

    Args:
        limit: Nombre de recettes à retourner
        filtre_realisable: Ne garder que les recettes réalisables

    Returns:
        Liste de recommandations
    """
    from models.models import Recette

    moteur = creer_moteur_recommandation_standard()

    moteur.configurer_criteres({
        'saison': 1.0,
        'disponibilite': 0.9,
        'variete': 0.7,
        'cout': 0.3,
        'temps': 0.3,
        'nutrition': 0.2
    })

    recettes = Recette.query.all()

    return moteur.recommander(
        recettes,
        limit=limit,
        filtre_realisable=filtre_realisable
    )
