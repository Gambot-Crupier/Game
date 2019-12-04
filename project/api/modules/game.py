from project.api.models import PlayerInGame, Round, Game
from project.api.modules.firebase import message_app
import requests, os, json, sys
from project import db

base_gateway_url = os.getenv('GAMBOT_GATEWAY_URL')

def check_active_players(game_id):
    players = PlayerInGame.query.filter_by(game_id = game_id, is_playing_match = True).all()
    number_of_players = len(players)
    print(number_of_players, file=sys.stderr)
    print(players[0].player_id, file=sys.stderr)

    if number_of_players < 2:
        url = base_gateway_url + 'get_user_by_id?user_id=' + str(players[0].player_id)
        get_player_request = requests.request("GET", url)
        print(get_player_request.status_code, file=sys.stderr)
        
        if get_player_request.status_code == 200:
            data = get_player_request.json()
            print(data, file=sys.stderr)

            data = {
                'message': 'Fugiram',
                'winner': data['player']['name']
            }

            message_app(data, game_id)

            check_endgame(players[0].player_id, game_id)

def check_endgame(winner_id, game_id):
    players = PlayerInGame.query.filter_by().all()
    defeated_players = PlayerInGame.query.filter_by(money = 0).all()

    if len(defeated_players) == (len(players) - 1):
        url = base_gateway_url + 'get_user_by_id?user_id=' + str(winner_id)
        get_player_request = requests.request("GET", url)
        data = get_player_request.json()

        game = Game.query.filter_by(id = game_id).first()
        game.winner = winner_id
        game.status = 3

        db.session.commit()

        data = {
            'message': 'Endgame',
            'winner': data['player']['name']
        }

        message_app(data, game_id)
    else:

        previous_round = Round.query.filter_by().all()
        previous_round = previous_round[-1]
        round_data = Round(game_id = game_id, small_blind = 250, big_blind = 500, bet = 500, current_player_id= -1)
        players_in_game = PlayerInGame.query.filter_by(game_id = game_id).all()

        for player in players_in_game:
            player.bet = 0
            player.is_playing_match = True
        
        winner = PlayerInGame.query.filter_by(player_id = winner_id).first()
        winner.money = winner.money + previous_round.total_bet_prize

        db.session.add(round_data)
        db.session.commit()

        data = {
            'message': 'NovoRound',
        }

        message_app(data, game_id)
        


def check_last_player_bet(round_id, player_id, game_id):
    print('checklastplayerbet', file = sys.stderr)
    round_data = Round.query.filter_by(id = round_id).first()
    game = Game.query.filter_by(status = 2).first()
    

    if round_data.last_player_raised_bet == player_id:
        print('requisisao', file = sys.stderr)
        url = base_gateway_url + 'get_round_cards_number?round_id=' + str(round_id)
        round_cards_request = requests.request("GET", url)
        cards_data = round_cards_request.json()


        if cards_data['number']['number'] < 5:
            round_data.distribute_cards = True
            game.continued = 3
            db.session.commit()
        else:
            url = base_gateway_url + 'get_winner'
            player_list = PlayerInGame.query.filter_by(game_id = game_id).all()
            
            request_data = {
                'round_id': round_id,
                'players': []
            }

            for player in player_list:
                player = { 'id': player.player_id }
                request_data['players'].append(player)

            print('\n\n\nRequest_data', file = sys.stderr)
            


            winner_request = requests.request("POST", url, json = request_data,
                                            headers = {'Accept': 'application/json', 'content-type' : 'application/json'})

            print(winner_request.status_code, file = sys.stderr)


            if winner_request.status_code == 200:
                request_data = winner_request.json()
                print(request_data, file = sys.stderr)

                url = base_gateway_url + 'get_user_by_id?user_id=' + str(request_data['winner'])
                get_player_request = requests.request("GET", url)

                player_data = get_player_request.json()

                data = {
                    'message': 'Endround',
                    'winner': player_data['player']['name']
                }

                message_app(data, game_id)

                game.continued = 4

                check_endgame(request_data['winner'], game_id)



    