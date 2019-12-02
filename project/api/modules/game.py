from project.api.models import PlayerInGame
from project.api.modules.firebase import message_app
import requests, os, json, sys

base_gateway_url = os.getenv('GAMBOT_GATEWAY_URL')

def check_active_players(game_id):
    players = PlayerInGame.query.filter_by(game_id = game_id, is_playing_match = True).all()
    number_of_players = len(players)

    if number_of_players < 2:
        url = base_gateway_url + 'get_user_by_id?user_id=' + str(players[0].player_id)
        get_player_request = requests.request("GET", url)
        
        if get_player_request.status_code == 200:
            data = get_player_request.json()

            data = {
                'message': 'Fugiram',
                'winner': data['player']['name']
            }

            message_app(data, game_id)

def check_last_player_bet(round_id, player_id):
    round_data = Round.query.filter_by(id = round_id).first()

    if round_data.check_last_player_bet == player_id:
        url = base_gateway_url + 'get_round_cards_number?round_id' + str(round_id)
        round_cards_request = requests.request("GET", url)
        cards_data = round_cards_request.json()

        if round_cards_request['number'] < 5:
            round_data.distribute_cards = True;
            db.session.commit()
        else:
            print('ganhar jogo')


    