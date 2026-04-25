import pytest
from app import create_app
from models.models import (
    db as _db, Ingredient, IngredientSaison, StockFrigo,
    Recette, EtapeRecette, IngredientRecette, RecettePlanifiee
)


@pytest.fixture
def app():
    application = create_app('testing')
    with application.app_context():
        _db.create_all()
        yield application
        _db.session.remove()
        _db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def ingredient(app):
    ing = Ingredient(nom='Tomate', unite='g', prix_unitaire=0.5, categorie='Légumes')
    _db.session.add(ing)
    _db.session.commit()
    return ing


@pytest.fixture
def ingredient_avec_stock(app, ingredient):
    stock = StockFrigo(ingredient_id=ingredient.id, quantite=300)
    _db.session.add(stock)
    _db.session.commit()
    return ingredient


@pytest.fixture
def recette(app, ingredient):
    r = Recette(nom='Salade tomate', type_recette='Entrée')
    _db.session.add(r)
    _db.session.flush()
    _db.session.add(IngredientRecette(recette_id=r.id, ingredient_id=ingredient.id, quantite=200))
    _db.session.add(EtapeRecette(recette_id=r.id, ordre=1, description='Couper les tomates'))
    _db.session.commit()
    return r
