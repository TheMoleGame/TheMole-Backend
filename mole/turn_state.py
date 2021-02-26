from enum import Enum


class GameOverReason(Enum):
    DEFAULT = 0
    REACHED_END_OF_MAP = 1
    MORIARTY_CAUGHT = 2


class MoveModifier(Enum):
    NORMAL = 0
    HINDER = 1
    SIMPLIFY = 2


class TurnState:
    class PlayerTurnState(Enum):
        PLAYER_CHOOSING = 0
        PLAYER_CHOOSING_OCCASION = 1
        PLAYING_MINIGAME = 2
        DEVIL_MOVE = 3
        GAME_OVER = 4

    def __init__(self):
        self.player_index = 0
        self.player_turn_state = TurnState.PlayerTurnState.PLAYER_CHOOSING
        self.occasion_choices = None

    def start_minigame(self):
        self.player_turn_state = TurnState.PlayerTurnState.PLAYING_MINIGAME

    def choosing_occasion(self, occasion_choices):
        self.player_turn_state = TurnState.PlayerTurnState.PLAYER_CHOOSING_OCCASION
        self.occasion_choices = occasion_choices

    def game_over(self):
        self.player_turn_state = TurnState.PlayerTurnState.GAME_OVER
        self.occasion_choices = None

    def to_dict(self):
        return {
            'player_index': self.player_index,
            'player_turn_state': self.player_turn_state.name,
            'occasion_choices': self.occasion_choices,
        }

    def __repr__(self):
        parts = ['(player_index: {}  state: {}'.format(self.player_index, self.player_turn_state.name)]
        if self.occasion_choices is not None:
            parts.append(str(self.occasion_choices))
        return '  '.join(parts) + ')'