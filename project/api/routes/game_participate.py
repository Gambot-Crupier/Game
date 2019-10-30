from flask import Blueprint, jsonify, request
from os.path import join, dirname, realpath
from requests.exceptions import HTTPError
from project.api.models import Game, PlayerInGame
from project import db
import json, sys
from sqlalchemy import update

player_in_game_blueprint = Blueprint('player_in_game', __name__)

# Game Status
# 1 = Iniciando
# 2 = Em progresso
# 3 = Finalizado

@player_in_game_blueprint.route('/post_player_in_game', methods=['POST'])
def post_game_participate():
    try:    
        game_participate_json = request.get_json()    
        player_id = game_participate_json['player_id']
    
        game_starting = Game.query.filter_by(status = 1).first()  
        
        # Caso não haja um jogo no estado Iniciando
        if game_starting is None:

            game_in_progress = Game.query.filter_by(status = 2).first() 

            # Caso não haja um jogo nem iniciando e nem em progresso, inicia-se um
            if game_in_progress is None:
                new_game = Game()
                db.session.add(new_game)

                db.session.flush()
                db.session.refresh(new_game)                
                
                db.session.add(PlayerInGame(game_id=new_game.id, player_id=player_id))
            
            # Caso haja um jogo em progresso
            else:
                return jsonify({"message": "Game in Progress"}), 406
        
        # Caso haja um jogo no estado Iniciando
        else:
            db.session.add(PlayerInGame(game_id=game_starting.id, player_id=player_id))
             
        db.session.commit()

    except:
        return jsonify({"message": "Error on adding player to game"}), 500
    else:
        return jsonify({"message": "Player added to game"}), 200




@player_in_game_blueprint.route('/get_players_in_game', methods=['GET'])
def get_game_participate():
    try:
        game_starting = Game.query.filter_by(status = 1).first()
        game_in_progress = Game.query.filter_by(status = 2).first()

        game = game_starting if game_starting else (game_in_progress if game_in_progress else None)
        
        if game is None:
            return jsonify({"message": "No game found"}), 406
        
        response = {
            "game_id": game.id,
            "game_status": game.status,
            "players": []
        }

        players_in_game = PlayerInGame.query.filter_by(game_id=game.id).all()

        for player_in_game in players_in_game:
            response['players'].append({
                "player_id": player_in_game.player_id
            })

        return json.dumps(response), 200        

    except:
        return jsonify({"message": "Error retriving players"}), 500
    

@player_in_game_blueprint.route('/delete_player_in_game', methods=['DELETE'])
def delete_game_participate():
    try:
        player_id = request.args.get('player_id')
        game_id = request.args.get('game_id')
        
        player_in_game = PlayerInGame.query.filter_by(player_id=player_id, game_id=game_id).first()

        if not player_in_game:

            return jsonify({"message": "Player do not exists."})
        else:
            
            db.session.delete(player_in_game)
            return jsonify({"message": "Player deleted."})
        

        db.session.commit()
        
    except:
        return jsonify({"message": "Unable to deleted the player"}), 404


@player_in_game_blueprint.route('/start_game', methods=['POST'])
def start_game():
    try:
        game_starting = Game.query.filter_by(status = 1).first()
        if game_starting is None:
            return jsonify({"message": "No game is initializing"}), 406

        players = PlayerInGame.query.filter_by(game_id=game_starting.id).all()

        for player in players:
            player.money = 10000 # Valor Inicial de dinheiro dos jogadores

        game_starting.status = 2 # Status do jogo mudado para "Em Progresso"
        db.session.commit()

        return jsonify({"message": "Game Started"}), 200

    except Exception as e:
        return jsonify({"error": "Error on starting Game", "message": str(e)}), 500


@player_in_game_blueprint.route('/get_players_money', methods=['GET'])
def get_player_money():
    try:
        player_id = request.args.get('player_id')

        game = Game.query.filter_by(status=2).first()
        if game is None:
            return jsonify({"error": "No game in progress"}), 406

        player = PlayerInGame.query.filter_by(player_id=player_id, game_id=game.id).first()
        if player is not None:
            return jsonify({"player_id": player.player_id, "game_id": game.id, "money": player.money}), 200
        else:
            return jsonify({"error": "No player with this id found in current game"}), 406

    except Exception as e:
        return jsonify({"message": "Error on getting Player's Money", "error": str(e)}), 500
