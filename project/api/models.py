from sqlalchemy.sql import func
from project import db

# Game Status
# 1 = Iniciando
# 2 = Em progresso
# 3 = Finalizado

class Game(db.Model):
    id             = db.Column(db.Integer,  primary_key=True, autoincrement=True)
    winner         = db.Column(db.Integer)
    status    = db.Column(db.Integer, nullable= False)
    player_in_game = db.relationship('PlayerInGame', backref='game', lazy=True)
    
    def __init__(self):
        self.status  = 1
    
        
class PlayerInGame(db.Model):
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'), primary_key=True)
    player_id = db.Column(db.Integer, nullable=False, primary_key=True)
    
    def __init__(self, game_id, player_id):
        self.game_id = game_id
        self.player_id = player_id