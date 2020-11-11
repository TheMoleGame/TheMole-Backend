from enum import Enum
from .models import Event, Evidence
from .game_character import Player
import random


def create_map():
    return []


class Game:
    def __init__(self):
        self.token = str(random.randrange(1000, 10000))  # type: str
        self.position = 0
        self.players = []
        self.running = False
        self.team_pos = Field()
        # create Evidence combination
        self.puzzle = []
        self.puzzle.append(Evidence("Frau Tippie", "P"))
        self.puzzle.append(Evidence("Bathtub", "L"))
        self.puzzle.append(Evidence("Revolver", "W"))
        self.map = create_map()

    def start_game(self, players):
        # init players,
        # for(player in players):
        #   # player. teampos.
        #    player,player.getMove())
        # start a round
        #   move player1
        #   move player2
        #   moveDevil
        pass

    def add_player(self, sid, name):
        if self.running is False:
            player = Player(name, sid)
            self.players.append(player)
        else:
            pass

    @staticmethod
    def move(distance, character):
        character.move(distance)

    @staticmethod
    def debug_map():
        return "dddds-SM"

    def get_player(self, sid):
        for player in self.players:
            if player.sid == sid:
                return player
        return None

    def player_choice(self, sio, _sid, player_choice):
        """
        This event is called, if a player chose one of:
         - dice:
            player_choice is in the following form:
            {
                'type': 'dice',
                'value': 6,
            }

         - sharing evidence:
            player_choice is in the following form:
            {
                'type': 'share-evidence',
                'with': player_name,
                'evidence': evidence_name,
            }

         - validating evidence:
            player_choice is in the following form:
            {
                'type': 'validate-evidence',
                'evidences': [evidence_name1, evidence_name2, ...],
            }

         - searches for evidence:
            player_choice is in the following form:
            {
                'type': 'search-evidence',
                'success': true/false,
            }
        """
        if player_choice.get('type') == 'dice':
            self.send_to_all(sio, 'move', int(player_choice.get('value')))
            # TODO: apply movement to own data
        elif player_choice.get('type') == 'share-evidence':
            pass  # TODO
        elif player_choice.get('type') == 'validate-evidence':
            pass  # TODO
        elif player_choice.get('type') == 'search-evidence':
            pass  # TODO

    def player_occasion_choice(self, sid, chosen_occasion):
        """
        This event is called, if a player chose an occasion.

        :param chosen_occasion: The name of the occasion
        :type chosen_occasion: str
        """
        # emit info event to the caller (or all clients?)
        # save buffs/new evidences/new position/debuffs for next round

    def send_to_all(self, sio, event, message=None):
        """
        Sends a message to all players in the game
        """
        print('sending to room')
        if message is None:
            sio.emit(event, room=self.token)
        else:
            sio.emit(event, message, room=self.token)


class FieldType(Enum):
    WALKABLE = 1
    EVENT = 2
    MINIGAME = 3
    DEVIL_FIELD = 4
    SHORTCUT = 5


class Field:
    def __init__(self, previous_field=None, next_field=None, shortcut_field=None, field_type=FieldType.WALKABLE, has_team=False, has_devil=False):
        self.previous_field = previous_field    # type: Field
        self.next_field = next_field            # type: Field
        self.shortcut_field = shortcut_field    # type: Field
        self.type = field_type                  # type: FieldType
        self.has_team = has_team                # type: bool
        self.has_devil = has_devil              # type: bool

    def get_next(self):
        if self.shortcut_field is not None:
            return Event("Minigame X", "Would you rather mit zwei personen")
        return self.next_field