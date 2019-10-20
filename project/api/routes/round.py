from flask import Blueprint, jsonify, request
from os.path import join, dirname, realpath
from requests.exceptions import HTTPError
from project.api.models import Game, PlayerInGame, Round
from project import db
import json, sys
from sqlalchemy import update

round_blueprint = Blueprint('round', __name__)

@round_blueprint.route('/create_round', methods=['POST'])
def create_round():
    try:
        game = Game.query.filter_by(status = 2).first()
        if game is not None:
            round_data = Round(game_id = game.id, small_blind = 250, big_blind = 500, bet_prize = 5000)
            db.session.add(round_data)
            db.session.commit()

            # TODO: Colocar requisição do firebase aqui

            return jsonify({

            }), 200
        else:
            return jsonify({
                "message": "Não existe jogo ativo"
            })
    except:
        return jsonify({
            "message": "Erro ao criar o round!"
        }), 400