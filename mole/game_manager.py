import random

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

    def add_player(self, sio, sid, name):
        player_id = len(self.players)
        self.players.append({'player_id': player_id, 'sid': sid, 'name': name})

        # send player information to all players
        player_info = list(map(lambda p: {'name': p['name'], 'player_id': p['player_id']}, self.players))
        sio.emit(
            'player_infos',
            player_info,
            room=self.token
        )

    def __str__(self):
        return 'Game(token={}  num_players={})'.format(self.token, len(self.players))

    def __repr__(self):
        return str(self)


class GameManager:
    def __init__(self):
        self.games = {}  # maps sids to games
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

    def start_game(self, sio, sid, token, start_position=None):
        pending_game = self.get_pending_by_token(token)

        if pending_game is None:
            raise Exception('No pending game for token: {}. Maybe the game is already running?'.format(token))

        if len(pending_game.players) < 3:
            raise Exception('Cannot start game with less than 3 players')

        if not pending_game.host_sid == sid:
            raise Exception('Invalid token sid combination. Only the host can start the game.')

        game = Game(sio, pending_game.token, pending_game.host_sid, pending_game.players, start_position)
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

    def remove_user(self, sid):
        if sid in self.games:
            del self.games[sid]
