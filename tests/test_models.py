"""Tests unitaires des modèles SQLAlchemy."""
import pytest
from models.models import (
    db, Ingredient, IngredientSaison, StockFrigo,
    Recette, EtapeRecette, IngredientRecette, RecettePlanifiee
)


class TestIngredientUnites:
    def test_get_quantite_en_grammes_unite_g(self, app, ingredient):
        assert ingredient.get_quantite_en_grammes(150) == 150

    def test_get_quantite_en_grammes_unite_ml(self, app):
        ing = Ingredient(nom='Lait', unite='ml')
        assert ing.get_quantite_en_grammes(200) == 200

    def test_get_quantite_en_grammes_unite_piece_avec_poids(self, app):
        ing = Ingredient(nom='Oeuf', unite='pièce', poids_piece=60)
        db.session.add(ing)
        db.session.commit()
        assert ing.get_quantite_en_grammes(3) == 180

    def test_get_quantite_en_grammes_piece_sans_poids(self, app):
        ing = Ingredient(nom='Pomme', unite='pièce', poids_piece=None)
        assert ing.get_quantite_en_grammes(2) == 2


class TestIngredientPrix:
    def test_calculer_prix_simple(self, app, ingredient):
        # Tomate : 0.5€/g, 200g → 100€ (prix stocké par unité native)
        assert ingredient.calculer_prix(200) == pytest.approx(100.0)

    def test_calculer_prix_zero(self, app, ingredient):
        assert ingredient.calculer_prix(0) == 0.0

    def test_calculer_prix_unitaire_nul(self, app):
        ing = Ingredient(nom='Eau', unite='ml', prix_unitaire=0)
        assert ing.calculer_prix(500) == 0.0


class TestIngredientSaisons:
    def test_get_saisons_vide(self, app, ingredient):
        assert ingredient.get_saisons() == []

    def test_set_get_saisons(self, app, ingredient):
        ingredient.set_saisons(['printemps', 'ete'])
        db.session.commit()
        assert set(ingredient.get_saisons()) == {'printemps', 'ete'}

    def test_est_de_saison_vrai(self, app, ingredient):
        ingredient.set_saisons(['hiver'])
        db.session.commit()
        assert ingredient.est_de_saison('hiver') is True

    def test_est_de_saison_faux(self, app, ingredient):
        ingredient.set_saisons(['hiver'])
        db.session.commit()
        assert ingredient.est_de_saison('ete') is False

    def test_est_de_saison_sans_restriction(self, app, ingredient):
        # Sans saison définie → disponible toute l'année
        assert ingredient.est_de_saison('printemps') is True

    def test_set_saisons_ecrase_les_anciennes(self, app, ingredient):
        ingredient.set_saisons(['printemps', 'ete'])
        db.session.commit()
        ingredient.set_saisons(['automne'])
        db.session.commit()
        assert ingredient.get_saisons() == ['automne']


class TestIngredientNutrition:
    def test_get_nutrition_for_quantity(self, app):
        ing = Ingredient(nom='Riz', unite='g', calories=130, proteines=2.7, glucides=28, lipides=0.3)
        db.session.add(ing)
        db.session.commit()
        nutrition = ing.get_nutrition_for_quantity(100)
        assert nutrition['calories'] == pytest.approx(130)
        assert nutrition['proteines'] == pytest.approx(2.7)

    def test_get_nutrition_quantite_differente(self, app):
        ing = Ingredient(nom='Riz', unite='g', calories=130)
        db.session.add(ing)
        db.session.commit()
        nutrition = ing.get_nutrition_for_quantity(50)
        assert nutrition['calories'] == pytest.approx(65)


class TestRecetteCalculs:
    def test_temps_total(self, app):
        r = Recette(nom='Quiche', temps_preparation=15, temps_cuisson=30)
        assert r.temps_total() == 45

    def test_temps_total_sans_cuisson(self, app):
        r = Recette(nom='Salade', temps_preparation=10, temps_cuisson=None)
        assert r.temps_total() == 10

    def test_temps_total_sans_aucun(self, app):
        r = Recette(nom='Tartine', temps_preparation=None, temps_cuisson=None)
        assert r.temps_total() is None

    def test_calculer_cout(self, app, recette, ingredient):
        # ingredient: 0.5€/g × 200g = 100€
        cout = recette.calculer_cout()
        assert cout == pytest.approx(100.0)

    def test_calculer_cout_recette_vide(self, app):
        r = Recette(nom='Vide')
        db.session.add(r)
        db.session.commit()
        assert r.calculer_cout() == 0.0


class TestRecetteDisponibilite:
    def test_realisable_avec_stock_suffisant(self, app, recette, ingredient):
        stock = StockFrigo(ingredient_id=ingredient.id, quantite=500)
        db.session.add(stock)
        db.session.commit()
        dispo = recette.calculer_disponibilite_ingredients()
        assert dispo['realisable'] is True
        assert dispo['ingredients_manquants'] == []

    def test_non_realisable_sans_stock(self, app, recette, ingredient):
        dispo = recette.calculer_disponibilite_ingredients()
        assert dispo['realisable'] is False
        assert len(dispo['ingredients_manquants']) == 1

    def test_non_realisable_stock_insuffisant(self, app, recette, ingredient):
        stock = StockFrigo(ingredient_id=ingredient.id, quantite=50)  # besoin: 200
        db.session.add(stock)
        db.session.commit()
        dispo = recette.calculer_disponibilite_ingredients()
        assert dispo['realisable'] is False


class TestCascadeDelete:
    def test_suppression_ingredient_supprime_stock(self, app, ingredient_avec_stock):
        ingredient_id = ingredient_avec_stock.id
        db.session.delete(ingredient_avec_stock)
        db.session.commit()
        assert StockFrigo.query.filter_by(ingredient_id=ingredient_id).first() is None

    def test_suppression_ingredient_supprime_saisons(self, app, ingredient):
        ingredient.set_saisons(['printemps', 'ete'])
        db.session.commit()
        ingredient_id = ingredient.id
        db.session.delete(ingredient)
        db.session.commit()
        assert IngredientSaison.query.filter_by(ingredient_id=ingredient_id).count() == 0

    def test_suppression_recette_supprime_etapes(self, app, recette):
        recette_id = recette.id
        db.session.delete(recette)
        db.session.commit()
        assert EtapeRecette.query.filter_by(recette_id=recette_id).count() == 0

    def test_suppression_recette_supprime_ingredients(self, app, recette):
        recette_id = recette.id
        db.session.delete(recette)
        db.session.commit()
        assert IngredientRecette.query.filter_by(recette_id=recette_id).count() == 0

    def test_suppression_recette_supprime_planifications(self, app, recette):
        planif = RecettePlanifiee(recette_id=recette.id)
        db.session.add(planif)
        db.session.commit()
        recette_id = recette.id
        db.session.delete(recette)
        db.session.commit()
        assert RecettePlanifiee.query.filter_by(recette_id=recette_id).count() == 0
