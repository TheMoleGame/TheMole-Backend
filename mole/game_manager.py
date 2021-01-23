import random
import sys
from typing import Dict

from .game import Game


class PendingGame:
    def __init__(self, host_sid, token):
        """
        :type host_sid: str
        :type token: str
        """
        self.token = token
        self.host_sid = host_sid
        self.players = []

    def _set_player_ids(self):
        for player_id, player in enumerate(self.players):
            player['player_id'] = player_id

    def add_player(self, sio, sid, name):
        self.players.append({'player_id': 0, 'sid': sid, 'name': name})
        self._set_player_ids()
        self.send_player_infos(sio)

    def send_player_infos(self, sio):
        # send player information to all players
        player_info = list(map(lambda p: {'name': p['name'], 'player_id': p['player_id']}, self.players))
        sio.emit(
            'player_infos',
            player_info,
            room=self.token
        )

    def remove_player(self, sio, sid):
        # remove player with matching sid
        removed_players = list(filter(lambda p: p['sid'] == sid, self.players))
        self.players = list(filter(lambda p: p['sid'] != sid, self.players))
        self._set_player_ids()
        self.send_player_infos(sio)
        for removed_player in removed_players:
            print('Removed "{}" from game {}'.format(removed_player['name'], self.token))
        if len(removed_players) >= 2:
            print('WARN: removed more than one player', file=sys.stderr)

    def __str__(self):
        return 'Game(token={}  num_players={})'.format(self.token, len(self.players))

    def __repr__(self):
        return str(self)


class GameManager:
    def __init__(self):
        self.games: Dict[str, Game] = {}  # maps sids to running games
        self.pending_games = []
        self.taken_tokens = []  # type: list[int]

    def _create_new_token(self) -> str:
        def _token_possible(t):
            return t not in self.taken_tokens

        possible_tokens = list(filter(_token_possible, range(1000, 10000)))  # remove all tokens already used
        token = random.choice(possible_tokens)
        self.taken_tokens.append(token)
        return str(token)

    def create_game(self, host_sid):
        token = self._create_new_token()
        pending_game = PendingGame(host_sid, token)
        self.pending_games.append(pending_game)
        return pending_game.token

    def start_game(self, sio, sid, token, start_position=None, test_choices=None):
        pending_game = self.get_pending_by_token(token)

        if pending_game is None:
            raise Exception('No pending game for token: {}. Maybe the game is already running?'.format(token))

        if len(pending_game.players) < 3:
            raise Exception('Cannot start game with less than 3 players')

        if not pending_game.host_sid == sid:
            raise Exception('Invalid token sid combination. Only the host can start the game.')

        game = Game(sio, pending_game.token, pending_game.host_sid, pending_game.players, start_position, test_choices)
        for player in pending_game.players:
            self.games[player['sid']] = game

        self.remove_pending_game(token)

    def remove_pending_game(self, token):
        self.pending_games = list(filter(lambda pg: pg.token != token, self.pending_games))

    def get_pending_by_token(self, token):
        for pending_game in self.pending_games:
            if pending_game.token == token:
                return pending_game

        return None

    def get(self, sid) -> Game:
        return self.games.get(sid)

    def handle_rejoin(self, sio, sid, token, name):
        game = None
        for g in self.games.values():
            if g.token == token:
                game = g
        if game is None:
            return False
        if not game.has_disconnected_player(name):
            print(
                'Player failed to join game "{}", because of using unknown name "{}"'
                .format(game.token, name),
                file=sys.stderr
            )
            return False
        game.player_rejoin(sio, sid, name)
        self.games[sid] = game
        return True

    def handle_join(self, sio, sid, token, name):
        pending_game = self.get_pending_by_token(token)

        if pending_game is None:
            if self.handle_rejoin(sio, sid, token, name):
                sio.enter_room(sid, token)
            else:
                sio.emit('join_failed', 'No game found with token "{}"!'.format(token), room=sid)
                raise Exception(
                    'ERROR: join game with token {} could not be found for player with sid {}'.format(token, sid)
                )
        else:
            if len(pending_game.players) >= 8:
                sio.emit('join_failed', 'Game "{}" is full!'.format(token), room=sid)
                raise Exception('ERROR: Player "{}" cannot join game "{}" as it is full.'.format(name, token))

            sio.enter_room(sid, pending_game.token)

            pending_game.add_player(sio, sid, name)

            print('player "{}" added to game {}'.format(name, pending_game.token), file=sys.stderr)

    def handle_disconnect(self, sio, sid):
        # remove from pending games
        for pending_game in self.pending_games:
            for player_index, player in enumerate(pending_game.players):
                if player['sid'] == sid:
                    pending_game.remove_player(sio, sid)
                    break

        # remove from running games
        game = self.games.get(sid)
        if game is not None:
            if game.host_sid == sid:
                # TODO: Host cannot rejoin at the moment
                print('Host disconnected for game {}'.format(game.token), file=sys.stderr)
                return
            game.player_disconnect(sio, sid)
