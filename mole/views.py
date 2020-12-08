import os
import sys

import socketio
from django.http import HttpResponse
from .game_manager import GameManager
from .db_init import *


sio = socketio.Server(async_mode=None, cors_allowed_origins='*')
basedir = os.path.dirname(os.path.realpath(__file__))
games = GameManager()

# db_init()


def index(_request):
    return HttpResponse(open(os.path.join(basedir, 'static/index.html')))


@sio.event
def disconnect(sid):
    games.remove_user(sid)


@sio.event
def create_game(sid, _message):
    token = games.create_game(sid)

    # game host also joins room for debugging
    sio.enter_room(sid, token)

    return token


@sio.event
def start_game(sid, message):
    assert isinstance(message, str)
    print('starting game {}'.format(message))
    games.start_game(sio, sid, token=message)


@sio.event
def join_game(sid, message):
    try:
        token = message['token']
        name = message['name']
    except KeyError as e:
        raise Exception('ERROR: invalid login message: {}'.format(repr(e)))
    except TypeError:
        raise Exception('ERROR: message is not an object. Got {} instead'.format(message))

    pending_game = games.get_pending_by_token(token)

    if pending_game is None:
        raise Exception('ERROR: invalid token: {}'.format(token))

    sio.enter_room(sid, pending_game.token)

    pending_game.add_player(sid, name)

    print('player "{}" added to game {}'.format(name, pending_game.token), file=sys.stderr)


@sio.event
def player_choice(sid, message):
    game = games.get(sid)

    if game is None:
        print('ERROR(player_choice): no game found for sid {}'.format(sid), file=sys.stderr)
        return False

    game.player_choice(sio, sid, message)

    return True


@sio.event
def player_occasion_choice(sid, message):
    game = games.get(sid)

    if game is None:
        print('ERROR(player_occasion_choice): no game found for sid {}'.format(sid), file=sys.stderr)
        return False

    game.player_occasion_choice(sio, sid, message)
