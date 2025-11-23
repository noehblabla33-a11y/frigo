from app import create_app
from models.models import db
from flask_migrate import Migrate

app = create_app()
migrate = Migrate(app, db) 

if __name__ == "__main__":
    app.run()

#### Comment mettre à jour la DB
## flask --app manage.py db migrate -m "Commentaire"
## flask --app manage.py db upgrade
