from flask import Blueprint, jsonify, request
from os.path import join, dirname, realpath
from requests.exceptions import HTTPError
from project.api.models import Game, PlayerInGame
from project import db
import json, sys
from sqlalchemy import update

player_in_game_blueprint = Blueprint('player_in_game', __name__)

@player_in_game_blueprint.route('/post_player_in_game', methods=['POST'])
def post_game_participate():
    try:    
        game_participate_json = request.get_json()
        
        player_id = game_participate_json['player_id']
    
        game = Game.query.filter_by(status = 1).first()
        
        if game is None:
            game_in_progress = Game.query.filter_by(status = 2).first() 
            print(game_in_progress, file = sys.stderr)
        
            if game_in_progress is None:
                game = Game()
                db.session.add(game)
                db.session.commit()
                
            else:
                return jsonify({"message": "Jogo em Progresso!"}), 406
        
        else:
            db.session.update(PlayerInGame(game_id=game.id, player_id=player_id))   
            
        db.session.add(PlayerInGame(game_id=game.id, player_id=player_id))
        
        db.session.commit()

    except HTTPError:
        return jsonify({"message": "NOT FOUND"}), 404
    else:
        return jsonify({"message": "Player in game Recived"}), 200