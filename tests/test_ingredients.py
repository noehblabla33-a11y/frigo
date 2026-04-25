"""Tests de non-régression des routes CRUD des ingrédients."""
import pytest
from models.models import db, Ingredient, IngredientSaison, StockFrigo


BASE = '/ingredients'


def form_ingredient(**kwargs):
    """Construit des données de formulaire pour un ingrédient."""
    defaults = {
        'nom': 'Carotte',
        'unite': 'g',
        'prix_unitaire': '0.3',
        'categorie': 'Légumes',
    }
    defaults.update(kwargs)
    return defaults


class TestCreationIngredient:
    def test_creation_simple_redirige(self, client):
        resp = client.post(f'{BASE}/', data=form_ingredient())
        assert resp.status_code == 302

    def test_creation_persiste_en_base(self, client, app):
        client.post(f'{BASE}/', data=form_ingredient(nom='Courgette'))
        with app.app_context():
            assert Ingredient.query.filter_by(nom='Courgette').first() is not None

    def test_creation_champs_corrects(self, client, app):
        client.post(f'{BASE}/', data=form_ingredient(nom='Poireau', unite='g', prix_unitaire='1.2', categorie='Légumes'))
        with app.app_context():
            ing = Ingredient.query.filter_by(nom='Poireau').first()
            assert ing.unite == 'g'
            assert ing.prix_unitaire == pytest.approx(1.2)
            assert ing.categorie == 'Légumes'

    def test_creation_avec_saisons(self, client, app):
        data = form_ingredient(nom='Asperge')
        data['saison_printemps'] = 'on'
        data['saison_ete'] = 'on'
        client.post(f'{BASE}/', data=data)
        with app.app_context():
            ing = Ingredient.query.filter_by(nom='Asperge').first()
            assert set(ing.get_saisons()) == {'printemps', 'ete'}

    def test_creation_sans_saison(self, client, app):
        client.post(f'{BASE}/', data=form_ingredient(nom='Sel'))
        with app.app_context():
            ing = Ingredient.query.filter_by(nom='Sel').first()
            assert ing.get_saisons() == []

    def test_creation_nom_vide_non_bloque_par_route(self, client, app):
        # La route utilise validate_unique_ingredient (pas validate_ingredient_form),
        # qui ne vérifie pas le nom vide — comportement actuel à connaître.
        client.post(f'{BASE}/', data=form_ingredient(nom=''))
        with app.app_context():
            assert Ingredient.query.filter_by(nom='').count() == 1

    def test_creation_nom_duplique_bloque(self, client, app, ingredient):
        client.post(f'{BASE}/', data=form_ingredient(nom='Tomate'))
        with app.app_context():
            assert Ingredient.query.filter_by(nom='Tomate').count() == 1

    def test_creation_avec_nutrition(self, client, app):
        data = form_ingredient(nom='Poulet', unite='g')
        data.update({'calories': '165', 'proteines': '31', 'glucides': '0', 'lipides': '3.6'})
        client.post(f'{BASE}/', data=data)
        with app.app_context():
            ing = Ingredient.query.filter_by(nom='Poulet').first()
            assert ing.calories == pytest.approx(165)
            assert ing.proteines == pytest.approx(31)


class TestModificationIngredient:
    def test_modification_nom(self, client, app, ingredient):
        client.post(f'{BASE}/modifier/{ingredient.id}', data=form_ingredient(nom='Tomate cerise'))
        with app.app_context():
            ing = db.session.get(Ingredient, ingredient.id)
            assert ing.nom == 'Tomate cerise'

    def test_modification_prix(self, client, app, ingredient):
        client.post(f'{BASE}/modifier/{ingredient.id}', data=form_ingredient(nom='Tomate', prix_unitaire='1.5'))
        with app.app_context():
            ing = db.session.get(Ingredient, ingredient.id)
            assert ing.prix_unitaire == pytest.approx(1.5)

    def test_modification_met_a_jour_saisons(self, client, app, ingredient):
        data = form_ingredient(nom='Tomate')
        data['saison_ete'] = 'on'
        client.post(f'{BASE}/modifier/{ingredient.id}', data=data)
        with app.app_context():
            ing = db.session.get(Ingredient, ingredient.id)
            assert ing.get_saisons() == ['ete']

    def test_modification_supprime_anciennes_saisons(self, client, app, ingredient):
        # Ajouter des saisons initiales
        with app.app_context():
            ing = db.session.get(Ingredient, ingredient.id)
            ing.set_saisons(['printemps', 'ete', 'automne'])
            db.session.commit()
        # Modifier sans cocher aucune saison
        client.post(f'{BASE}/modifier/{ingredient.id}', data=form_ingredient(nom='Tomate'))
        with app.app_context():
            ing = db.session.get(Ingredient, ingredient.id)
            assert ing.get_saisons() == []

    def test_modification_nom_duplique_bloque(self, client, app, ingredient):
        autre = Ingredient(nom='Aubergine', unite='g')
        with app.app_context():
            db.session.add(autre)
            db.session.commit()
            autre_id = autre.id
        client.post(f'{BASE}/modifier/{ingredient.id}', data=form_ingredient(nom='Aubergine'))
        with app.app_context():
            # L'ingrédient original ne doit pas avoir changé de nom
            ing = db.session.get(Ingredient, ingredient.id)
            assert ing.nom == 'Tomate'

    def test_modification_ingredient_inexistant_retourne_404(self, client):
        resp = client.post(f'{BASE}/modifier/9999', data=form_ingredient())
        assert resp.status_code == 404


class TestSuppressionIngredient:
    def test_suppression_redirige(self, client, ingredient):
        resp = client.get(f'{BASE}/supprimer/{ingredient.id}')
        assert resp.status_code == 302

    def test_suppression_supprime_de_la_base(self, client, app, ingredient):
        ing_id = ingredient.id
        client.get(f'{BASE}/supprimer/{ingredient.id}')
        with app.app_context():
            assert db.session.get(Ingredient, ing_id) is None

    def test_suppression_supprime_les_saisons(self, client, app, ingredient):
        with app.app_context():
            ing = db.session.get(Ingredient, ingredient.id)
            ing.set_saisons(['hiver'])
            db.session.commit()
            ing_id = ingredient.id
        client.get(f'{BASE}/supprimer/{ingredient.id}')
        with app.app_context():
            assert IngredientSaison.query.filter_by(ingredient_id=ing_id).count() == 0

    def test_suppression_supprime_le_stock(self, client, app, ingredient_avec_stock):
        ing_id = ingredient_avec_stock.id
        client.get(f'{BASE}/supprimer/{ingredient_avec_stock.id}')
        with app.app_context():
            assert StockFrigo.query.filter_by(ingredient_id=ing_id).first() is None

    def test_suppression_ingredient_inexistant_retourne_404(self, client):
        resp = client.get(f'{BASE}/supprimer/9999')
        assert resp.status_code == 404


class TestListeIngredients:
    def test_liste_retourne_200(self, client):
        resp = client.get(f'{BASE}/')
        assert resp.status_code == 200

    def test_liste_filtre_par_search(self, client, app, ingredient):
        resp = client.get(f'{BASE}/?search=Tomate')
        assert resp.status_code == 200

    def test_liste_filtre_par_saison(self, client):
        resp = client.get(f'{BASE}/?saison=ete')
        assert resp.status_code == 200
