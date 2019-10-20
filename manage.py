from flask.cli import FlaskGroup
from project import create_app, db
from project.api.models import Game
import firebase_admin

app = create_app()
firebase_admin.initialize_app()
cli = FlaskGroup(create_app=create_app)

# Recreates Database
@cli.command()
def recreatedb():
    db.drop_all()
    db.create_all()
    db.session.commit()


if __name__ == '__main__':
    cli()