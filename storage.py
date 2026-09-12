games = {}

def get_game(chat_id):
    return games.get(chat_id)

def create_game(chat_id):
    games[chat_id] = {
        "players": {},
        "phase": "lobby",
        "day": 0,
        "night_actions": {},
        "votes": {},
        "votes_msg_id": None,
        "sergeant_promoted": False,
    }
    return games[chat_id]

def end_game(chat_id):
    games.pop(chat_id, None)
