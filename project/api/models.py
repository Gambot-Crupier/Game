from sqlalchemy.sql import func
from project import db

# Game Status
# 1 = Iniciando
# 2 = Em progresso
# 3 = Finalizado

class Game(db.Model):
    id = db.Column(db.Integer,  primary_key=True, autoincrement=True, unique = True)
    winner = db.Column(db.Integer)
    status = db.Column(db.Integer, nullable= False)
    player_in_game = db.relationship('PlayerInGame', backref='game', lazy=True)
    rounds = db.relationship('Round')
    continued = db.Column(db.Integer, nullable= False)

    def __init__(self):
        self.status  = 1
        self.continued = 0


class PlayerInGame(db.Model):
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'), primary_key=True)
    player_id = db.Column(db.Integer, nullable=False, primary_key=True)
    device_id = db.Column(db.String(255), nullable=False)
    money = db.Column(db.Integer, default = 5000)
    bet = db.Column(db.Float, default=0)
    is_playing_match = db.Column(db.Boolean, default=True)
    position = db.Column(db.Integer)

    def __init__(self, game_id, player_id, device_id):
        self.game_id = game_id
        self.player_id = player_id
        self.device_id = device_id


class Round(db.Model):
    total_bet_prize = db.Column(db.Float, default=0)
    bet = db.Column(db.Float, nullable = False)
    winner = db.Column(db.Integer, nullable = True)
    small_blind = db.Column(db.Float, nullable = False)
    big_blind = db.Column(db.Float, nullable = False)
    id = db.Column(db.Integer, nullable = False, autoincrement = True, primary_key = True, unique = True)
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'))
    last_player_raised_bet = db.Column(db.Integer)
    distribute_cards = db.Column(db.Boolean, default=True)
    current_player_id = db.Column(db.Integer, default=0)
