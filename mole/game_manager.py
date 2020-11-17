from .game import Game


class GameManager:
    def __init__(self):
        self.games = {}  # maps sids to games
        self.pending_games = []

    def create_game(self):
        game = Game()
        self.pending_games.append(game)
        return game

    def add_user(self, game, sid, name):
        self.games[sid] = game
        game.add_player(sid, name)

    def get_by_token(self, token):
        for game in self.pending_games:
            if game.token == token:
                return game

        for sid, game in self.games.items():
            if game.token == token:
                return game

        return None

    def get(self, sid):
        """
        :rtype: Game
        """
        return self.games.get(sid)

    def remove_user(self, sid):
        if sid in self.games:
            del self.games[sid]
