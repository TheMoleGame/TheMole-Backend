import enum
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
        self.available_tokens = list(range(1000, 10000))

    def _create_new_token(self) -> str:
        if not self.available_tokens:
            raise AllTokensTakenException('Cant create any more games. No tokens are available')
        token = random.choice(self.available_tokens)
        self.available_tokens.remove(token)
        return str(token)

    def is_game_running(self):
        return bool(self.games)

    def create_game(self, host_sid):
        token = self._create_new_token()
        pending_game = PendingGame(host_sid, token)
        self.pending_games.append(pending_game)
        return pending_game.token

    def start_game(
            self, sio, sid, token, start_position=None, test_choices=None, all_proofs=False, enable_minigames=False,
            moriarty_position=0
    ):
        pending_game = self.get_pending_by_token(token)

        if pending_game is None:
            raise StartGameException('No pending game for token: {}. Maybe the game is already running?'.format(token))

        if len(pending_game.players) < 3:
            raise StartGameException('Cannot start game with less than 3 players')

        if not pending_game.host_sid == sid:
            raise StartGameException('Invalid token sid combination. Only the host can start the game.')

        game = Game(
            sio, pending_game.token, pending_game.host_sid, pending_game.players, start_position, test_choices,
            all_proofs, enable_minigames, moriarty_position
        )
        for player in pending_game.players:
            self.games[player['sid']] = game

        self.remove_pending_game(token)

    def remove_pending_game(self, token):
        len_before = len(self.pending_games)
        self.pending_games = list(filter(lambda pg: pg.token != token, self.pending_games))
        if len_before != len(self.pending_games):
            self.available_tokens.append(int(token))

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
                break
        if game is None:
            raise JoinGameException(
                reason=JoinGameException.Reasons.GAME_NOT_FOUND,
                sid=sid,
                token=token,
                name=name,
            )
        if not game.has_disconnected_player(name):
            raise JoinGameException(
                reason=JoinGameException.Reasons.NAME_NOT_FOUND,
                sid=sid,
                token=token,
                name=name,
            )
        game.player_rejoin(sio, sid, name)
        self.games[sid] = game

    def handle_join(self, sio, sid, token, name):
        pending_game = self.get_pending_by_token(token)

        if pending_game is None:
            self.handle_rejoin(sio, sid, token, name)
            sio.enter_room(sid, token)
        else:
            if len(pending_game.players) >= 8:
                sio.emit('join_failed', 'Game "{}" is full!'.format(token), room=sid)
                raise JoinGameException(
                    reason=JoinGameException.Reasons.GAME_FULL,
                    sid=sid,
                    token=token,
                    name=name,
                )

            if name.lower() in map(lambda p: p['name'].lower(), pending_game.players):
                raise JoinGameException(
                    reason=JoinGameException.Reasons.NAME_DUPLICATION,
                    sid=sid,
                    token=token,
                    name=name,
                )

            sio.enter_room(sid, pending_game.token)

            pending_game.add_player(sio, sid, name)

            print('player "{}" added to game {}'.format(name, pending_game.token), file=sys.stderr)

    def _remove_game(self, token):
        print('Removing game {}.'.format(token), file=sys.stderr)
        len_before = len(self.games)
        self.games = {sid: game for sid, game in self.games.items() if game.token != token}
        if len_before != len(self.games):
            self.available_tokens.append(int(token))

    def handle_disconnect(self, sio, sid):
        # remove from pending games
        for pending_game in self.pending_games:
            for player_index, player in enumerate(pending_game.players):
                if player['sid'] == sid:
                    pending_game.remove_player(sio, sid)
                    break
            if pending_game.host_sid == sid:
                self.remove_pending_game(pending_game.token)
                print('INFO: removing pending game "{}"'.format(pending_game.token), file=sys.stderr)

        # remove from running games
        game = self.games.get(sid)
        if game is not None:
            if game.host_sid == sid:
                print('Host disconnected from game {}.'.format(game.token), file=sys.stderr)
                self._remove_game(game.token)
                return
            game.player_disconnect(sio, sid)
            if not game.has_connected_player():
                print('All players disconnected from game {}.'.format(game.token), file=sys.stderr)
                self._remove_game(game.token)


class JoinGameException(Exception):
    class Reasons(enum.Enum):
        GAME_NOT_FOUND = 0
        GAME_FULL = 1
        NAME_NOT_FOUND = 2
        NAME_DUPLICATION = 3

    def __init__(self, reason, sid=None, token=None, name=None):
        self.reason = reason
        self.player_sid = sid
        self.token = token
        self.name = name
        super().__init__('Join game failed: {}'.format(reason.name.lower()))


class AllTokensTakenException(Exception):
    pass


class StartGameException(Exception):
    pass
