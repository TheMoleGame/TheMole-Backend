import os

import socketio
from django.http import HttpResponse
from .game_manager import GameManager


sio = socketio.Server(async_mode=None)
basedir = os.path.dirname(os.path.realpath(__file__))
games = GameManager()


def index(_request):
    return HttpResponse(open(os.path.join(basedir, 'static/index.html')))


@sio.event
def disconnect(sid):
    games.remove_user(sid)


@sio.event
def create_game(sid, _message):
    game = games.create_game(sid)

    # game host also joins room for debugging
    sio.enter_room(sid, game.token)

    return game.token


@sio.event
def join_game(sid, message):
    try:
        token = message['token']
        name = message['name']
    except KeyError as e:
        print('ERROR: invalid login message: {}'.format(repr(e)))  # TODO: rework error message. Maybe with exceptions?
        return False
    except TypeError:
        print('ERROR: message is not an object. Got {} instead'.format(message))
        return False

    game = games.get_by_token(token)

    if game is None:
        print('ERROR: invalid token: {}'.format(token))
        return False

    sio.enter_room(sid, game.token)

    games.add_user(game, sid, name)
    return True


@sio.event
def player_choice(sid, message):
    game = games.get(sid)

    if game is None:
        print('ERROR: no game found for sid {}'.format(sid))
        return False

    game.player_choice(sio, sid, message)

    return True


@sio.event
def player_occasion_choice(sid, message):
    game = games.get(sid)

    if game is None:
        print('ERROR: no game found for sid {}'.format(sid))
        return False

    game.player_occasion_choice(sid, message)

