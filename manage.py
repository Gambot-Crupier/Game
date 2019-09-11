from flask.cli import FlaskGroup
from project import app, db
from project.api.models import Game


cli = FlaskGroup(app)

# Recreates Database
@cli.command()
def recreatedb():
    db.drop_all()
    db.create_all()
    db.session.commit()



if __name__ == '__main__':
    cli()