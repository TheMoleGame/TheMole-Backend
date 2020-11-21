from enum import Enum

from pyllist import dllistnode

from .game_character import *
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

    map_dll.append(Field(FieldType.WALKABLE))  # Team should be here
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
    init_f = Field(FieldType.DEVIL_FIELD)  # devil
    map_dll.append(init_f)

    for i in range(0, 3):
        map_dll.append(Field(FieldType.DEVIL_FIELD))

    map_dll.append(Field(FieldType.WALKABLE))  # team
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

    # for map_dll.iternodes(): todo

    return map_dll


class TurnState:
    class PlayerTurnState(Enum):
        PLAYER_CHOOSING = 0
        DEVIL_MOVE = 1

    def __init__(self):
        self.player_id = 0
        self.player_turn_state = TurnState.PlayerTurnState.PLAYER_CHOOSING

    def diced(self):
        self.player_id += 1
        self.player_turn_state = TurnState.PlayerTurnState.PLAYER_CHOOSING


class Game:
    def __init__(self, sio, token, host_sid, player_infos):
        self.host_sid = host_sid
        self.token = token
        self.players = []
        for player_info in player_infos:
            self.players.append(Player(player_info['name'], player_info['sid']))

        # Choose random mole
        random.choice(self.players).is_mole = True

        self.turn_state = TurnState()

        self.map = small_map()  # small test map
        self.team_pos: dllistnode = self.map.nodeat(4)
        self.devil_pos: dllistnode = self.map.nodeat(0)

        print(self.debug_game_representation())  # test case debug
        self.move(2, self.players[0])  # test case move

        #  create Evidence combination
        self.puzzle = []
        # self.puzzle.append(Evidence("Frau Tippie", "P"))
        # self.puzzle.append(Evidence("Bathtub", "L"))
        # self.puzzle.append(Evidence("Revolver", "W"))

        # TODO: Serialize Map and send with init packet
        for player in self.players:
            sio.emit('init', {'is_mole': player.is_mole, 'map': None}, room=player.sid)

        sio.emit('your_turn', '', room=self.players[0].sid)

    # @distance the fields to move
    # @character to move
    def move(self, distance, character):
        self.team_pos = character.move(self.team_pos, distance)

    def check_end_turn(self, sio):
        if self.turn_state.player_id == len(self.players):
            self.turn_state = TurnState()
            sio.emit('chaser_move', random.randint(1, 6), room=self.token)

    def debug_game_representation(self):
        result = ""
        for node in self.map.iternodes():  # iterate over list nodes
            field: Field = node.value
            result += ' - '+str(field.type.name)
            if node == self.team_pos:
                result += '+ Team'
            if node == self.devil_pos:
                result += '+ Devil'
            #  todo add change from numbers to characters
        return result

    def get_player(self, sid):
        for player in self.players:
            if player.sid == sid:
                return player
        return None

    def player_choice(self, sio, sid, player_choice):
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
        if not self.players_turn(sid):
            player = self.get_player(sid)
            player_name = '<unknown>' if player is None else player.name
            raise Exception('Got invalid event from player "{}"'.format(player_name))

        if player_choice.get('type') == 'dice':
            # TODO: apply movement to own data
            self.send_to_all(sio, 'move', int(player_choice.get('value')))
            self.turn_state.diced()
        elif player_choice.get('type') == 'share-evidence':
            pass  # TODO
        elif player_choice.get('type') == 'validate-evidence':
            pass  # TODO
        elif player_choice.get('type') == 'search-evidence':
            pass  # TODO

        self.check_end_turn(sio)

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
        if message is None:
            sio.emit(event, room=self.token)
        else:
            sio.emit(event, message, room=self.token)

    def players_turn(self, sid):
        return self.players[self.turn_state.player_id].sid == sid


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

