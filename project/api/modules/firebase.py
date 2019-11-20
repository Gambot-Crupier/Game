from firebase_admin import messaging


def subscribe_to_firebase(players_list, game_id):
    topic = 'Gambot'
    response = messaging.subscribe_to_topic(players_list, topic)
    print(response)

    return response

def message_app(self, data, game_id):
    topic = 'Gambot'
    
    message = messaging.Message(topic = topic, data = data)
    response = messaging.send(message)

    return response