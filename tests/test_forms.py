"""Tests unitaires des fonctions de parsing et validation de formulaires."""
import pytest
from utils.forms import (
    parse_float, parse_int, parse_int_or_none, parse_float_or_none,
    parse_positive_float, parse_positive_int, clean_string, clean_string_or_none,
    parse_recette_form, parse_ingredients_list, parse_etapes_list,
    validate_categorie, validate_type_recette,
    validate_unique_ingredient, validate_unique_recette,
    validate_quantite_positive,
)
from models.models import db, Ingredient, Recette


class TestParseFloat:
    def test_string_valide(self):
        assert parse_float('3.14') == pytest.approx(3.14)

    def test_string_vide(self):
        assert parse_float('') == 0.0

    def test_none(self):
        assert parse_float(None) == 0.0

    def test_espaces(self):
        assert parse_float('  2.5  ') == pytest.approx(2.5)

    def test_invalide_retourne_default(self):
        assert parse_float('abc', default=-1.0) == -1.0

    def test_entier_en_string(self):
        assert parse_float('42') == pytest.approx(42.0)

    def test_float_natif(self):
        assert parse_float(1.5) == pytest.approx(1.5)

    def test_int_natif(self):
        assert parse_float(3) == pytest.approx(3.0)


class TestParseInt:
    def test_string_valide(self):
        assert parse_int('42') == 42

    def test_string_vide(self):
        assert parse_int('') == 0

    def test_none(self):
        assert parse_int(None) == 0

    def test_float_string_tronque(self):
        assert parse_int('3.7') == 3

    def test_invalide_retourne_default(self):
        assert parse_int('xyz', default=-1) == -1


class TestParseIntOrNone:
    def test_valeur_valide(self):
        assert parse_int_or_none('10') == 10

    def test_string_vide_retourne_none(self):
        assert parse_int_or_none('') is None

    def test_none_retourne_none(self):
        assert parse_int_or_none(None) is None

    def test_invalide_retourne_none(self):
        assert parse_int_or_none('abc') is None


class TestParseFloatOrNone:
    def test_valeur_valide(self):
        assert parse_float_or_none('1.5') == pytest.approx(1.5)

    def test_vide_retourne_none(self):
        assert parse_float_or_none('') is None

    def test_none_retourne_none(self):
        assert parse_float_or_none(None) is None


class TestCleanString:
    def test_strip_espaces(self):
        assert clean_string('  bonjour  ') == 'bonjour'

    def test_none_retourne_default(self):
        assert clean_string(None, 'défaut') == 'défaut'

    def test_vide_retourne_default(self):
        assert clean_string('', 'défaut') == 'défaut'


class TestCleanStringOrNone:
    def test_valeur_normale(self):
        assert clean_string_or_none('  texte  ') == 'texte'

    def test_vide_retourne_none(self):
        assert clean_string_or_none('') is None

    def test_none_retourne_none(self):
        assert clean_string_or_none(None) is None


class TestParseRecetteForm:
    def test_parsing_complet(self):
        data = {
            'nom': 'Quiche',
            'instructions': 'Mélanger et cuire',
            'type_recette': 'Plat principal',
            'temps_preparation': '15',
            'temps_cuisson': '30',
        }
        result = parse_recette_form(data)
        assert result['nom'] == 'Quiche'
        assert result['instructions'] == 'Mélanger et cuire'
        assert result['type_recette'] == 'Plat principal'
        assert result['temps_preparation'] == 15
        assert result['temps_cuisson'] == 30

    def test_nom_manquant_leve_valueerror(self):
        with pytest.raises(ValueError):
            parse_recette_form({'nom': ''})

    def test_nom_none_leve_valueerror(self):
        with pytest.raises(ValueError):
            parse_recette_form({})

    def test_temps_optionnels(self):
        result = parse_recette_form({'nom': 'Salade', 'temps_preparation': '', 'temps_cuisson': ''})
        assert result['temps_preparation'] is None
        assert result['temps_cuisson'] is None

    def test_instructions_optionnelles(self):
        result = parse_recette_form({'nom': 'Tartine'})
        assert result['instructions'] is None


class TestParseIngredientsList:
    def test_parsing_un_ingredient(self):
        data = {'ingredient_0': '1', 'quantite_0': '200'}
        result = parse_ingredients_list(data)
        assert result == [(1, 200.0)]

    def test_parsing_plusieurs_ingredients(self):
        data = {
            'ingredient_0': '1', 'quantite_0': '100',
            'ingredient_1': '2', 'quantite_1': '50',
        }
        result = parse_ingredients_list(data)
        assert len(result) == 2
        assert (1, 100.0) in result
        assert (2, 50.0) in result

    def test_quantite_zero_ignoree(self):
        data = {'ingredient_0': '1', 'quantite_0': '0'}
        result = parse_ingredients_list(data)
        assert result == []

    def test_ingredient_id_manquant_arrete(self):
        data = {'ingredient_0': '1', 'quantite_0': '100', 'quantite_1': '50'}
        result = parse_ingredients_list(data)
        assert len(result) == 1

    def test_liste_vide(self):
        assert parse_ingredients_list({}) == []


class TestParseEtapesList:
    def test_parsing_une_etape(self):
        data = {'etape_desc_0': 'Couper les légumes'}
        result = list(parse_etapes_list(data))
        assert result == [('Couper les légumes', None)]

    def test_parsing_avec_duree(self):
        data = {'etape_desc_0': 'Cuire', 'etape_duree_0': '20'}
        result = list(parse_etapes_list(data))
        assert result == [('Cuire', 20)]

    def test_parsing_plusieurs_etapes(self):
        data = {
            'etape_desc_0': 'Préparer',
            'etape_desc_1': 'Cuire',
            'etape_desc_2': 'Servir',
        }
        result = list(parse_etapes_list(data))
        assert len(result) == 3

    def test_etape_vide_ignoree(self):
        data = {'etape_desc_0': 'Valide', 'etape_desc_1': ''}
        result = list(parse_etapes_list(data))
        assert len(result) == 1

    def test_liste_vide(self):
        assert list(parse_etapes_list({})) == []


@pytest.fixture
def request_ctx(app):
    """Contexte de requête HTTP pour les fonctions qui appellent flash()."""
    with app.test_request_context():
        yield


class TestValidateCategorie:
    CATEGORIES = [('Légumes', '🥕'), ('Fruits', '🍎'), ('Viandes', '🥩')]

    def test_categorie_valide(self, request_ctx):
        assert validate_categorie('Légumes', self.CATEGORIES) is True

    def test_categorie_invalide(self, request_ctx):
        assert validate_categorie('Inconnu', self.CATEGORIES) is False

    def test_categorie_none_acceptee(self, request_ctx):
        assert validate_categorie(None, self.CATEGORIES) is True

    def test_categorie_vide_acceptee(self, request_ctx):
        assert validate_categorie('', self.CATEGORIES) is True


class TestValidateTypeRecette:
    TYPES = ['Entrée', 'Plat principal', 'Dessert']

    def test_type_valide(self, request_ctx):
        assert validate_type_recette('Entrée', self.TYPES) is True

    def test_type_invalide(self, request_ctx):
        assert validate_type_recette('Inconnu', self.TYPES) is False

    def test_type_vide_accepte(self, request_ctx):
        assert validate_type_recette('', self.TYPES) is True


class TestValidateUniqueIngredient:
    def test_nom_unique(self, request_ctx):
        assert validate_unique_ingredient('NouveauIngredient') is True

    def test_nom_existant_bloque(self, request_ctx, ingredient):
        assert validate_unique_ingredient('Tomate') is False

    def test_nom_existant_avec_exclude_id(self, request_ctx, ingredient):
        # Modifier un ingrédient avec son propre nom doit être autorisé
        assert validate_unique_ingredient('Tomate', exclude_id=ingredient.id) is True


class TestValidateUniqueRecette:
    def test_nom_unique(self, request_ctx):
        assert validate_unique_recette('NouvelleRecette') is True

    def test_nom_existant_bloque(self, request_ctx, recette):
        assert validate_unique_recette('Salade tomate') is False

    def test_nom_existant_avec_exclude_id(self, request_ctx, recette):
        assert validate_unique_recette('Salade tomate', exclude_id=recette.id) is True


class TestValidateQuantitePositive:
    def test_quantite_positive(self, request_ctx):
        assert validate_quantite_positive(10.0) is True

    def test_quantite_zero_est_valide(self, request_ctx):
        # La fonction accepte 0 (condition : < 0, pas <= 0)
        assert validate_quantite_positive(0) is True

    def test_quantite_negative_invalide(self, request_ctx):
        assert validate_quantite_positive(-5) is False
