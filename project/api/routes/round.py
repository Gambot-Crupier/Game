from flask import Blueprint, jsonify, request
from os.path import join, dirname, realpath
from requests.exceptions import HTTPError
from project.api.models import Game, PlayerInGame, Round
from project.api.modules.firebase import subscribe_to_firebase, message_app
from project.api.modules.game import check_active_players, check_last_player_bet
from project import db
import json, sys
from sqlalchemy import update
import requests, os, json, sys

round_blueprint = Blueprint('round', __name__)
base_gateway_url = os.getenv('GAMBOT_GATEWAY_URL')

@round_blueprint.route('/get_round_id', methods=['GET'])
def get_id():
    round_data = Round.query.filter_by().all()

    return jsonify({
        'round_id': round_data[-1].id
    }), 200

# QUANDO O ROUND ACABAR: ZERAR PLAYER_IN_GAME.BET E PLAYER_IN_GAME.IS_PLAYING = TRUE
# QUADNO INICIAR O ROUND, DEVE SER COLOCADO O PRIMEIRO PLAYER A JOGAR COMO 'LAST_PLAYER_RAISED_BET'

@round_blueprint.route('/round_redirect', methods=['POST'])
def redirect_round():
    game = Game.query.filter_by(status = 2).first()

    data = {
        'message': 'Redireciona'
    }

    try:
        message_app(data, game.id)
    except Exception as e:
        return jsonify({
            'message': str(e)
        }), 400
    
    return jsonify({
        'message': 'Redirecionou'
    }), 200


@round_blueprint.route('/create_round', methods=['POST'])
def create_round():
    try:
        game = Game.query.filter_by(status = 2).first()

        if game is not None:
            round_data = Round(game_id = game.id, small_blind = 250, big_blind = 500, bet = 500)
            db.session.add(round_data)
            db.session.commit()

            # Zerar o valor da aposta do jogador e botar o atributo is_playing em 1

            return jsonify({
                "message": "Round Criado!"
            }), 200
        else:
            return jsonify({
                "message": "Não existe jogo ativo"
            }), 500
    except:
        return jsonify({
            "message": "Erro ao criar o round!"
        }), 500


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
        round_data = Round.query.filter_by(id=round_id).first()


        if round_data is not None:
            return jsonify({
                "round_id": round_data.id,
                "bet": round_data.bet
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
        data = request.get_json()

        game_id = data['game_id']
        player_id = data['player_id']
        round_id = data['round_id']
        player_in_game = PlayerInGame.query.filter_by(game_id=game_id, player_id=player_id).first()

        if player_in_game is not None:
            player_in_game.is_playing_match=False
            db.session.commit()
            
            data = {
                'message': 'Novo turno'
            }

            set_current_player_id(player_id, round_id)

            try:
                message_app(data, game_id)
            except Exception as e:
                return jsonify({
                    'message': str(e)
                }), 400
            
            check_last_player_bet(round_id, player_id, game_id)
            check_active_players(game_id)
            
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
        data = request.get_json()
        game_id = data['game_id']
        player_id = data['player_id']
        round_id = data['round_id']
        new_bet = int(data['value'])

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

                    set_current_player_id(player_id, round_id)

                    data = {
                        'message': 'Novo turno'
                    }

                    try:
                        message_app(data, game_id)
                    except Exception as e:
                        return jsonify({
                            'message': str(e)
                        }), 400

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
        data = request.get_json()
        game_id = data['game_id']
        player_id = data['player_id']
        round_id = data['round_id']

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

                check_last_player_bet(round_id, player_id, game_id)    
                set_current_player_id(player_id, round_id)

                data = {
                    'message': 'Novo turno'
                }

                try:
                    message_app(data, game_id)
                except Exception as e:
                    return jsonify({
                        'message': str(e)
                    }), 40
                return jsonify({"message":"All In!"}), 200
            else:
                current_round.total_bet_prize+=money_difference
                player_in_game.money-=money_difference
                player_in_game.bet=current_round.bet

                db.session.commit()
                check_last_player_bet(round_id, player_id, game_id)
                set_current_player_id(player_id, round_id)

                data = {
                        'message': 'Novo turno'
                    }

                try:
                    message_app(data, game_id)
                except Exception as e:
                    print(str(e), file = sys.stderr)
                    return jsonify({
                        'message': str(e)
                    }), 400
                return jsonify({"message":"Aposta paga!"}), 200

        else:
            return jsonify({ "message": "Jogador não está no jogo!" }), 400

    except Exception as e:
        print(str(e), file= sys.stderr)
        return jsonify({ 
            "error": "Erro ao tentar pagar a aposta!",
            "message": str(e)
        }), 400


# Distribuição
# 1 = Start
# 2 = Stop
# 3 = Go
# 4 = Reset

@round_blueprint.route('/get_continue', methods=['GET'])
def get_continue():
    try:
        game = Game.query.filter_by(status = 2).first()
        if game is not None:
            print(game, file = sys.stderr)
            game_data = Game.query.all()

            return jsonify({'continue': str(game_data[-1].continued)}), 200
        else:
            return jsonify({
                "message": "Não existe jogo ativo."
            }), 204

    except:
        return jsonify({
            "message": "Erro ao retornar as ações para eletronica."
        }), 500


@round_blueprint.route('/post_continue', methods=['POST'])
def post_continue():
    try:
        data = request.get_json()
        continued = data['continue']
        game = Game.query.filter_by(status = 2).first()  

        if game is not None:
            game.continued = continued
            db.session.commit()

            return jsonify({ "message": "Atributo mudado com sucesso." }), 200
        else:
            return jsonify({ "message": "Não existe jogo ativo." }), 400
    except Exception as e:
        print(e, file= sys.stderr)  
        return jsonify({ "message": "Erro ao tentar postar as ações." }), 400


@round_blueprint.route('/distribuite_cards', methods=['GET'])
def distribuite_cards():
    try:
        game = Game.query.filter_by(status = 2).first()
        if game is not None:
            round_data = Round.query.order_by(Round.id).all()
            return jsonify({'distribute_cards': str(round_data[-1].distribute_cards)}), 200

        else:
            return jsonify({
                "message": "Não existe jogo ativo."
            }), 500
    except:
        return jsonify({
            "message": "Erro ao tentar recuperar se as cartas devem ser distribuídas!"
        }), 500



@round_blueprint.route('/get_round', methods=['GET'])
def get_round():
    try:
        game = Game.query.filter_by(status = 2).first()

        if game is not None:
            round_data = Round.query.order_by(Round.id).all()
            current_round = round_data[-1]
            return jsonify(
                {
                    'id': current_round.id,
                    'game_id': current_round.game_id,
                    'last_player_raised_bet': current_round.last_player_raised_bet,
                    'distribute_cards': str(current_round.distribute_cards),
                    'winner': current_round.winner,
                }
            ), 200

        else:
            return jsonify({ "message": "Não existe jogo ativo." }), 500
    except:
        return jsonify({ "message": "Erro ao tentar recuperar round!" }), 500

@round_blueprint.route('/get_current_player', methods=['GET'])
def get_current_player():
    round_id = request.args.get('round_id')

    if round_id is not None:
        round_data = Round.query.filter_by(id = round_id).first()

        if round_data is not None:
            return jsonify({
                'current_player_id': round_data.current_player_id
            }), 200
        else:
            return jsonify({
                'message': 'Could not find round'
            }), 400
    else:
        return jsonify({
            'message': 'Invalid Arguments'
        }), 400

@round_blueprint.route('/post_player_position', methods=['POST'])
def post_player_position():
    try:
        data = request.get_json()
        
        player_id = data['player_id']
        
        game = Game.query.filter_by(status = 2).first()        

        if game is not None:
            players = PlayerInGame.query.filter(PlayerInGame.position != None).filter_by(game_id = game.id).order_by(PlayerInGame.position).all()

            if not players:
                player = PlayerInGame.query.filter_by(player_id = player_id).first()
                player.position = 1
            else:
                last_position = players[-1].position
                player = PlayerInGame.query.filter_by(player_id = player_id).first()
                if not player.position:
                    player.position = (last_position+1)
                
            db.session.commit()

            return jsonify({ "message": "Posição mudada com sucesso." }), 200
        else:
            return jsonify({ "message": "Não existe jogo ativo." }), 400
    except:
        return jsonify({ "message": "Erro ao tentar postar a posição do player." }), 400



def set_current_player_id(player_id, round_id):

    # Pega a posição deste player
    player = PlayerInGame.query.filter_by(player_id = player_id).first()
    current_position = player.position

    next_player = PlayerInGame.query.filter_by(position = (current_position + 1)).first()
    current_round = Round.query.filter_by(id=round_id).first()

    # Caso seja o último, não haverá next_player
    if not next_player:
        first_player = PlayerInGame.query.filter_by(position = 1).first()
        current_round.current_player_id = first_player.player_id
        is_playing_match = first_player.is_playing_match
        current_player = first_player.player_id
    else:
        current_round.current_player_id = next_player.player_id
        is_playing_match = next_player.is_playing_match
        current_player = next_player.player_id

    db.session.commit()

    if is_playing_match != True:
        set_current_player_id(current_player, round_id)


@round_blueprint.route('/start_round', methods=['POST'])
def start_round():
    try:
        game = Game.query.filter_by(status = 2).first()

        if game is not None:
            rounds = Round.query.order_by(Round.id).all()
            print(game.id, file=sys.stderr)
            current_round = rounds[-1]
            print(current_round, file=sys.stderr)

            initial_player = PlayerInGame.query.filter_by(position=1, game_id=game.id).first()
            current_round.current_player_id = initial_player.player_id

            db.session.commit()
            data = {
                'message': 'Redireciona'
            }

            try:
                message_app(data, game.id)
            except Exception as e:
                return jsonify({
                'message': str(e)
            }), 400

            return jsonify({ "message": "Round começou!" }), 200

        else:
            return jsonify({ "message": "Não existe jogo ativo." }), 500
    except Exception as e:
        print(e, file=sys.stderr)
        return jsonify({ "message": "Erro ao tentar recuperar round!" }), 500