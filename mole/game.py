from enum import Enum

from pyllist import dllistnode

from .game_character import *
from .models import Evidence, Event
import random
import pyllist


def small_map():
    #  https://pythonhosted.org/pyllist/
    map_dll = pyllist.dllist()  # double linked List
    #  First Field
    init_f = Field(FieldType.DEVIL_FIELD)  # devil should start here
    map_dll.append(init_f)

    for i in range(0, 3):
        map_dll.append(Field(FieldType.DEVIL_FIELD))

    map_dll.append(Field(FieldType.WALKABLE))  #  Team should be here
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.EVENT))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.EVENT))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.MINIGAME))
    map_dll.append(Field(FieldType.Goal))

    return map_dll


def create_big_map():
    map_dll = pyllist.dllist()  # double linked List
    #  First Field
    init_f = Field(FieldType.DEVIL_FIELD, has_devil=True)
    map_dll.append(init_f)

    for i in range(0, 3):
        map_dll.append(Field(FieldType.DEVIL_FIELD))

    map_dll.append(Field(FieldType.WALKABLE, has_team=True))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.EVENT))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.EVENT))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.MINIGAME))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.EVENT))
    map_dll.append(Field(FieldType.EVENT))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.EVENT))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.MINIGAME))
    map_dll.append(Field(FieldType.EVENT))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.EVENT))
    map_dll.append(Field(FieldType.EVENT))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.EVENT))
    map_dll.append(Field(FieldType.SHORTCUT))  # todo.shortcut_field(Field)
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.EVENT))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.EVENT))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.EVENT))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.EVENT))
    map_dll.append(Field(FieldType.EVENT))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.EVENT))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.SHORTCUT))  # todo.shortcut_field(Field)
    map_dll.append(Field(FieldType.EVENT))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.EVENT))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.EVENT))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.EVENT))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.EVENT))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.EVENT))
    map_dll.append(Field(FieldType.SHORTCUT))  # todo.shortcut_field(Field)
    map_dll.append(Field(FieldType.EVENT))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.EVENT))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.EVENT))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.EVENT))
    map_dll.append(Field(FieldType.Goal))

    #for map_dll.iternodes(): todo


    return map_dll


class Game:
    def __init__(self):
        self.token = str(random.randrange(1000, 10000))  # type: str
        self.players = []
    #  player constructor (self, name, sid, is_mole=False):
        self.players.append(Player("Host", 23))  # fake sid
        self.my_turn = self.players[0]  # ich bin drann

        self.running = False
        self.map = small_map()  # small test map
        self.team_pos: dllistnode = self.map.nodeat(4)
        self.devil_pos: dllistnode = self.map.nodeat(0)

        self.debug_game_representation(self.map)  # test case debug
        #
        self.move(2, self.players[0])  # test case move

        #  create Evidence combination
        self.puzzle = []
        self.puzzle.append(Evidence("Frau Tippie", "P"))
        self.puzzle.append(Evidence("Bathtub", "L"))
        self.puzzle.append(Evidence("Revolver", "W"))

    def start_game(self, players):
        # init players, setMole
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

    # @distance the fields to move
    # @character to move
    def move(self, distance, character):
        self.team_pos = character.move(self.team_pos, distance)

    #@staticmethod
    def debug_game_representation(self, lst: pyllist.dllist):
        result = ""
        for node in lst.iternodes():  # iterate over list nodes
            if node == self.team_pos:
                result += 'T'
            if node == self.devil_pos:
                result += 'D'
            node: Field
            result += ''+str(node.value.type)
            #  todo add change from numbers to characters
        return result

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
    Goal = 6


class Field:
    counter = 0

    def __init__(self, field_type=FieldType.WALKABLE, shortcut_field=None):
        self.index = Field.counter
        Field.counter = Field.counter + 1
        self.shortcut_field = shortcut_field    # type: pyllist.dllist
        self.type = field_type                  # type: FieldType

