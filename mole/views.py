import os
import sys
import threading
import time

import socketio
from django.http import HttpResponse
from .game_manager import GameManager


TICK_INTERVAL = 1.0


sio = socketio.Server(async_mode=None, cors_allowed_origins='*')
basedir = os.path.dirname(os.path.realpath(__file__))
games = GameManager()

tick_thread = None


def tick_games():
    while games.is_game_running():
        ticked_tokens = set()
        # tick every game only once
        for game in games.games.values():
            if game.token not in ticked_tokens:
                game.tick(sio)
                ticked_tokens.add(game.token)
        time.sleep(TICK_INTERVAL)

    print('no games running -> stopping tick thread')
    global tick_thread
    tick_thread = None


def _start_tick_thread():
    global tick_thread
    tick_thread = threading.Thread(target=tick_games)
    tick_thread.start()


def index(_request):
    return HttpResponse(open(os.path.join(basedir, 'static/index.html')))


@sio.event
def create_game(sid, _message):
    token = games.create_game(sid)

    # game host also joins room for debugging
    sio.enter_room(sid, token)

    print('Created game "{}"'.format(token), file=sys.stderr)

    return token


@sio.event
def start_game(sid, message):
    token = None
    start_position = None
    test_choices = None
    all_proofs = False
    enable_minigames = True

    if isinstance(message, str):
        token = message
    elif isinstance(message, dict):
        token = message.get('token')
        start_position = message.get('startposition')
        test_choices = message.get('test_choices')
        all_proofs = message.get('all_proofs')
        enable_minigames = message.get('enable_minigames', True)

    print('starting game {}'.format(token))
    games.start_game(
        sio, sid, token=token, start_position=start_position, test_choices=test_choices, all_proofs=all_proofs,
        enable_minigames=enable_minigames
    )

    if tick_thread is None:
        _start_tick_thread()


@sio.event
def join_game(sid, message):
    try:
        token = message['token']
        name = message['name']
    except KeyError as e:
        raise Exception('ERROR: invalid login message: {}'.format(repr(e)))
    except TypeError:
        raise Exception('ERROR: message is not an object. Got {} instead'.format(message))

    if not name:
        raise Exception('ERROR: Cant join with empty name.')

    games.handle_join(sio, sid, token, name)


@sio.event
def disconnect(sid):
    games.handle_disconnect(sio, sid)


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


@sio.event
def pantomime_choice(sid, message):
    game = games.get(sid)

    if game is None:
        print('ERROR(pantomime_choice): no game found for sid {}'.format(sid), file=sys.stderr)
        return False

    game.pantomime_choice(sio, sid, message)


@sio.event
def pantomime_start(sid, message):
    game = games.get(sid)
    if game is None:
        print('ERROR(pantomime_choice): no game found for sid {}'.format(sid), file=sys.stderr)
        return False

    if message != '':
        print('ERROR(pantomime_start): message is not an empty string', file=sys.stderr)
        return False

    game.pantomime_start(sio, sid)
