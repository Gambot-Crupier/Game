from flask import Blueprint, jsonify, request
from os.path import join, dirname, realpath
from requests.exceptions import HTTPError
from project.api.models import Game, PlayerInGame, Round
from project.api.modules.firebase import subscribe_to_firebase, message_app
from project import db
import json, sys
from sqlalchemy import update
import requests, os, json, sys

round_blueprint = Blueprint('round', __name__)
base_gateway_url = os.getenv('GAMBOT_GATEWAY_URL')

# QUANDO O ROUND ACABAR: ZERAR PLAYER_IN_GAME.BET E PLAYER_IN_GAME.IS_PLAYING = TRUE
# QUADNO INICIAR O ROUND, DEVE SER COLOCADO O PRIMEIRO PLAYER A JOGAR COMO 'LAST_PLAYER_RAISED_BET'

@round_blueprint.route('/create_round', methods=['POST'])
def create_round():
    try:
        game = Game.query.filter_by(status = 2).first()
        if game is not None:
            round_data = Round(game_id = game.id, small_blind = 250, big_blind = 500, bet = 5000)
            db.session.add(round_data)
            db.session.commit()

            # TODO: Pegar device_id dos jogadores para criar tópico
            player_list = PlayerInGame.query(device_id).filter_by(game_id = game.id).all()

            # Zerar o valor da aposta do jogador e botar o atributo is_playing em 1


            # TODO: Colocar requisição do firebase aqui
            message_app('redirect', game.id)

            return jsonify({
                "message": "Round Criado!"
            }), 200
        else:
            return jsonify({
                "message": "Não existe jogo ativo"
            })
    except:
        return jsonify({
            "message": "Erro ao criar o round!"
        }), 400


@round_blueprint.route('/get_player_money', methods=['GET'])
def get_player_money():
    try:
        player_id = request.args.get('player_id')
        game_id = request.args.get('game_id')
        player_in_game = PlayerInGame.query.filter_by(player_id=player_id, game_id=game_id).first()

        if player_in_game is not None:
            return jsonify({
                "player_id": player_id,
                "game_id": game_id,
                "money": player_in_game.money
            }), 200
        else:
            return jsonify({ "message": "Player not found on this game." }), 404
    except Exception as e:
        return jsonify({ 
            "error": "Error on trying to retrive player's money..",
            "message": str(e)
        }), 400



@round_blueprint.route('/get_round_bet', methods=['GET'])
def get_round_bet():
    try:
        round_id = request.args.get('round_id')
        round = Round.query.filter_by(id=round_id).first()

        if round is not None:
            return jsonify({
                "round_id": round.id,
                "bet": round.bet
            }), 200
        else:
            return jsonify({ "message": "Round not found." }), 404

    except Exception as e:
        return jsonify({ 
            "error": "Error on trying to retrive round's bet..",
            "message": str(e)
        }), 400


@round_blueprint.route('/get_player_bet', methods=['GET'])
def get_player_bet():
    try:
        game_id = request.args.get('game_id')
        player_id = request.args.get('player_id')
        player_in_game = PlayerInGame.query.filter_by(game_id=game_id, player_id=player_id).first()

        if player_in_game is not None:
            return jsonify({
                "game_id": player_in_game.game_id,
                "player_id": player_in_game.player_id,
                "bet": player_in_game.bet
            }), 200
        else:
            return jsonify({ "message": "Jogador não está no jogo!." }), 404

    except Exception as e:
        return jsonify({ 
            "error": "Erro ao tentar recuprar as apostas do jogador",
            "message": str(e)
        }), 400



@round_blueprint.route('/leave_match', methods=['POST'])
def leave_match():
    try:
        game_id = request.args.get('game_id')
        player_id = request.args.get('player_id')
        player_in_game = PlayerInGame.query.filter_by(game_id=game_id, player_id=player_id).first()

        if player_in_game is not None:
            player_in_game.is_playing_match=False
            db.session.commit()
            message_app(player_id, game.id)
            return jsonify({"message":"Jogador fugiu da partida!"}), 200
        else:
            return jsonify({ "message": "Jogador não está no jogo!" }), 400

    except Exception as e:
        return jsonify({ 
            "error": "Erro ao tentar tirar jogador da partida!",
            "message": str(e)
        }), 400



@round_blueprint.route('/raise_bet', methods=['POST'])
def raise_bet():
    try:
        game_id = request.args.get('game_id')
        player_id = request.args.get('player_id')
        round_id = request.args.get('round_id')
        new_bet = int(request.args.get('value'))

        player_in_game = PlayerInGame.query.filter_by(game_id=game_id, player_id=player_id).first()
        current_round = Round.query.filter_by(id=round_id).first() 

        if player_in_game is not None:
            if new_bet > player_in_game.bet:
                money_difference = new_bet - player_in_game.bet

                if player_in_game.money > money_difference:
                    player_in_game.bet=new_bet
                    player_in_game.money-=money_difference

                    current_round.last_player_raised_bet=player_id
                    current_round.bet=new_bet
                    current_round.total_bet_prize+=money_difference
                    
                    db.session.commit()
                    return jsonify({"message":"Aposta Aumentada!"}), 200
                else:
                    return jsonify({"message":"Você não possui dinheiro para aumentar tanto a aposta. Tente pagá-la."}), 500

            else:
                return jsonify({"message":"Valor passado é menor ou igual ao valor da sua aposta."}), 400

        else:
            return jsonify({ "message": "Jogador não está no jogo!" }), 400

    except Exception as e:
        return jsonify({ 
            "error": "Erro ao tentar aumentar a aposta!",
            "message": str(e)
        }), 400



@round_blueprint.route('/pay_bet', methods=['POST'])
def pay_bet():
    try:
        game_id = request.args.get('game_id')
        player_id = request.args.get('player_id')
        round_id = request.args.get('round_id')


        player_in_game = PlayerInGame.query.filter_by(game_id=game_id, player_id=player_id).first()
        current_round = Round.query.filter_by(id=round_id).first()

        if player_in_game is not None:
            money_difference = current_round.bet - player_in_game.bet

            # Caso seja All In
            if player_in_game.money < money_difference:
                current_round.total_bet_prize+=player_in_game.money
                player_in_game.bet+=player_in_game.money
                player_in_game.money=0

                db.session.commit()
                return jsonify({"message":"All In!"}), 200
            else:
                current_round.total_bet_prize+=money_difference
                player_in_game.money-=money_difference
                player_in_game.bet=current_round.bet

                db.session.commit()
                return jsonify({"message":"Aposta paga!"}), 200

        else:
            return jsonify({ "message": "Jogador não está no jogo!" }), 400

    except Exception as e:
        return jsonify({ 
            "error": "Erro ao tentar pagar a aposta!",
            "message": str(e)
        }), 400