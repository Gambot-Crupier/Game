from flask import Blueprint, jsonify, request
from os.path import join, dirname, realpath
from requests.exceptions import HTTPError
from project.api.models import Game, PlayerInGame, Round
from project.api.modules.firebase import create_topic, message_app
from project import db
import json, sys
from sqlalchemy import update
import requests, os, json, sys

round_blueprint = Blueprint('round', __name__)
base_gateway_url = os.getenv('GAMBOT_GATEWAY_URL')

@round_blueprint.route('/create_round', methods=['POST'])
def create_round():
    try:
        game = Game.query.filter_by(status = 2).first()
        if game is not None:
            round_data = Round(game_id = game.id, small_blind = 250, big_blind = 500, bet_prize = 5000)
            db.session.add(round_data)

            # TODO: Pegar device_id dos jogadores para criar tópico
            player_list = PlayerInGame.query.filter_by(game_id = game.id).all()
            request_url = base_gateway_url + 'device_id_list'

            db.session.commit()
            # Zerar o valor da aposta do jogador e botar o atributo is_playing em 1


            # TODO: Colocar requisição do firebase aqui
            create_topic(player_list, game.id)
            message_app('Comece o jogo', game.id)

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