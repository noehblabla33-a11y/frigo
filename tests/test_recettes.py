"""Tests de non-régression des routes CRUD des recettes."""
import pytest
from models.models import db, Recette, EtapeRecette, IngredientRecette, RecettePlanifiee


BASE = '/recettes'


def form_recette(**kwargs):
    """Construit des données de formulaire pour une recette."""
    defaults = {
        'nom': 'Ratatouille',
        'type_recette': 'Plat principal',
        'instructions': 'Couper et cuire les légumes.',
        'temps_preparation': '20',
        'temps_cuisson': '40',
    }
    defaults.update(kwargs)
    return defaults


def ajouter_ingredients(data, *paires):
    """Ajoute des paires (ingredient_id, quantite) au formulaire."""
    for i, (ing_id, qte) in enumerate(paires):
        data[f'ingredient_{i}'] = str(ing_id)
        data[f'quantite_{i}'] = str(qte)
    return data


def ajouter_etapes(data, *descriptions):
    """Ajoute des étapes au formulaire."""
    for i, desc in enumerate(descriptions):
        data[f'etape_desc_{i}'] = desc
    return data


class TestCreationRecette:
    def test_creation_simple_redirige(self, client):
        resp = client.post(f'{BASE}/', data=form_recette())
        assert resp.status_code == 302

    def test_creation_persiste_en_base(self, client, app):
        client.post(f'{BASE}/', data=form_recette(nom='Gratin dauphinois'))
        with app.app_context():
            assert Recette.query.filter_by(nom='Gratin dauphinois').first() is not None

    def test_creation_champs_corrects(self, client, app):
        client.post(f'{BASE}/', data=form_recette(nom='Soupe', type_recette='Soupe', temps_preparation='10', temps_cuisson='25'))
        with app.app_context():
            r = Recette.query.filter_by(nom='Soupe').first()
            assert r.type_recette == 'Soupe'
            assert r.temps_preparation == 10
            assert r.temps_cuisson == 25

    def test_creation_avec_ingredient(self, client, app, ingredient):
        data = form_recette(nom='Salade')
        ajouter_ingredients(data, (ingredient.id, 150))
        client.post(f'{BASE}/', data=data)
        with app.app_context():
            r = Recette.query.filter_by(nom='Salade').first()
            assert len(r.ingredients) == 1
            assert r.ingredients[0].quantite == pytest.approx(150)
            assert r.ingredients[0].ingredient_id == ingredient.id

    def test_creation_avec_plusieurs_ingredients(self, client, app, ingredient):
        ing2 = Ingredient_fixture(app, 'Huile', 'ml', 0.01)
        data = form_recette(nom='Vinaigrette')
        ajouter_ingredients(data, (ingredient.id, 100), (ing2.id, 30))
        client.post(f'{BASE}/', data=data)
        with app.app_context():
            r = Recette.query.filter_by(nom='Vinaigrette').first()
            assert len(r.ingredients) == 2

    def test_creation_avec_etapes(self, client, app):
        data = form_recette(nom='Omelette')
        ajouter_etapes(data, 'Battre les oeufs', 'Chauffer la poêle', 'Verser et cuire')
        client.post(f'{BASE}/', data=data)
        with app.app_context():
            r = Recette.query.filter_by(nom='Omelette').first()
            assert len(r.etapes) == 3
            assert r.etapes[0].description == 'Battre les oeufs'

    def test_creation_nom_vide_bloque(self, client, app):
        client.post(f'{BASE}/', data=form_recette(nom=''))
        with app.app_context():
            assert Recette.query.filter_by(nom='').count() == 0

    def test_creation_nom_duplique_bloque(self, client, app, recette):
        client.post(f'{BASE}/', data=form_recette(nom='Salade tomate'))
        with app.app_context():
            assert Recette.query.filter_by(nom='Salade tomate').count() == 1

    def test_creation_type_invalide_bloque(self, client, app):
        client.post(f'{BASE}/', data=form_recette(nom='Inconnue', type_recette='TypeInexistant'))
        with app.app_context():
            assert Recette.query.filter_by(nom='Inconnue').first() is None


class TestModificationRecette:
    def test_modification_nom(self, client, app, recette):
        client.post(f'{BASE}/modifier/{recette.id}', data=form_recette(nom='Salade niçoise'))
        with app.app_context():
            r = db.session.get(Recette, recette.id)
            assert r.nom == 'Salade niçoise'

    def test_modification_metadonnees(self, client, app, recette):
        client.post(f'{BASE}/modifier/{recette.id}', data=form_recette(
            nom='Salade tomate', temps_preparation='5', temps_cuisson='0'
        ))
        with app.app_context():
            r = db.session.get(Recette, recette.id)
            assert r.temps_preparation == 5

    def test_modification_remplace_ingredients(self, client, app, recette, ingredient):
        ing2 = Ingredient_fixture(app, 'Basilic', 'g', 0.1)
        data = form_recette(nom='Salade tomate')
        ajouter_ingredients(data, (ing2.id, 10))
        client.post(f'{BASE}/modifier/{recette.id}', data=data)
        with app.app_context():
            r = db.session.get(Recette, recette.id)
            ids = [ir.ingredient_id for ir in r.ingredients]
            assert ingredient.id not in ids
            assert ing2.id in ids

    def test_modification_remplace_etapes(self, client, app, recette):
        data = form_recette(nom='Salade tomate')
        ajouter_etapes(data, 'Laver', 'Assaisonner')
        client.post(f'{BASE}/modifier/{recette.id}', data=data)
        with app.app_context():
            r = db.session.get(Recette, recette.id)
            assert len(r.etapes) == 2
            assert r.etapes[0].description == 'Laver'

    def test_modification_supprime_etapes_si_aucune(self, client, app, recette):
        client.post(f'{BASE}/modifier/{recette.id}', data=form_recette(nom='Salade tomate'))
        with app.app_context():
            r = db.session.get(Recette, recette.id)
            assert len(r.etapes) == 0

    def test_modification_recette_inexistante_retourne_404(self, client):
        resp = client.post(f'{BASE}/modifier/9999', data=form_recette())
        assert resp.status_code == 404

    def test_modification_nom_duplique_non_bloque_par_route(self, client, app, recette):
        # La route de modification n'appelle pas validate_unique_recette —
        # le renommage vers un nom existant est accepté par le code actuel.
        autre = Recette(nom='Gratin')
        with app.app_context():
            db.session.add(autre)
            db.session.commit()
        client.post(f'{BASE}/modifier/{recette.id}', data=form_recette(nom='Gratin'))
        with app.app_context():
            r = db.session.get(Recette, recette.id)
            assert r.nom == 'Gratin'


class TestSuppressionRecette:
    def test_suppression_redirige(self, client, recette):
        resp = client.get(f'{BASE}/supprimer/{recette.id}')
        assert resp.status_code == 302

    def test_suppression_supprime_de_la_base(self, client, app, recette):
        r_id = recette.id
        client.get(f'{BASE}/supprimer/{recette.id}')
        with app.app_context():
            assert db.session.get(Recette, r_id) is None

    def test_suppression_supprime_les_etapes(self, client, app, recette):
        r_id = recette.id
        client.get(f'{BASE}/supprimer/{recette.id}')
        with app.app_context():
            assert EtapeRecette.query.filter_by(recette_id=r_id).count() == 0

    def test_suppression_supprime_les_ingredients(self, client, app, recette):
        r_id = recette.id
        client.get(f'{BASE}/supprimer/{recette.id}')
        with app.app_context():
            assert IngredientRecette.query.filter_by(recette_id=r_id).count() == 0

    def test_suppression_supprime_les_planifications(self, client, app, recette):
        with app.app_context():
            planif = RecettePlanifiee(recette_id=recette.id)
            db.session.add(planif)
            db.session.commit()
            r_id = recette.id
        client.get(f'{BASE}/supprimer/{recette.id}')
        with app.app_context():
            assert RecettePlanifiee.query.filter_by(recette_id=r_id).count() == 0

    def test_suppression_recette_inexistante_retourne_404(self, client):
        resp = client.get(f'{BASE}/supprimer/9999')
        assert resp.status_code == 404


class TestListeRecettes:
    def test_liste_retourne_200(self, client):
        assert client.get(f'{BASE}/').status_code == 200

    def test_liste_filtre_par_type(self, client):
        assert client.get(f'{BASE}/?type=Entrée').status_code == 200

    def test_detail_recette(self, client, recette):
        assert client.get(f'{BASE}/{recette.id}').status_code == 200

    def test_detail_recette_inexistante_retourne_404(self, client):
        assert client.get(f'{BASE}/9999').status_code == 404


# Helper pour créer un ingrédient directement en base dans les tests
from models.models import Ingredient

def Ingredient_fixture(app, nom, unite='g', prix=0.0):
    with app.app_context():
        ing = Ingredient(nom=nom, unite=unite, prix_unitaire=prix)
        db.session.add(ing)
        db.session.commit()
        db.session.refresh(ing)
        return ing
