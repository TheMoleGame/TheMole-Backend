from enum import Enum
import random

from pyllist import dllist, dllistnode
import dj_database_url
from .game_character import *
from .models import *
from mole_backend.settings import DATABASES, db_from_env


def small_map():
    # reset counter
    Field.counter = 0

    #  https://pythonhosted.org/pyllist/
    map_dll = dllist()  # double linked List
    #  First Field
    init_f = Field(FieldType.DEVIL_FIELD)  # devil should start here
    map_dll.append(init_f)

    for i in range(0, 3):
        map_dll.append(Field(FieldType.DEVIL_FIELD))

    map_dll.append(Field(FieldType.WALKABLE))  # Team should be here
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.OCCASION))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.OCCASION))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.MINIGAME))
    map_dll.append(Field(FieldType.GOAL))

    return map_dll


def create_big_map():
    # reset counter
    Field.counter = 0

    map_dll = dllist()  # double linked List
    #  First Field
    init_f = Field(FieldType.DEVIL_FIELD)  # devil
    map_dll.append(init_f)

    for i in range(0, 3):
        map_dll.append(Field(FieldType.DEVIL_FIELD))

    map_dll.append(Field(FieldType.WALKABLE))  # team
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.OCCASION))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.OCCASION))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.MINIGAME))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.OCCASION))
    map_dll.append(Field(FieldType.OCCASION))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.OCCASION))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.MINIGAME))
    map_dll.append(Field(FieldType.OCCASION))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.OCCASION))
    map_dll.append(Field(FieldType.OCCASION))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.OCCASION))
    map_dll.append(Field(FieldType.SHORTCUT))  # todo.shortcut_field(Field)
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.OCCASION))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.OCCASION))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.OCCASION))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.OCCASION))
    map_dll.append(Field(FieldType.OCCASION))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.OCCASION))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.SHORTCUT))  # todo.shortcut_field(Field)
    map_dll.append(Field(FieldType.OCCASION))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.OCCASION))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.OCCASION))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.OCCASION))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.OCCASION))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.OCCASION))
    map_dll.append(Field(FieldType.SHORTCUT))  # todo.shortcut_field(Field)
    map_dll.append(Field(FieldType.OCCASION))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.OCCASION))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.OCCASION))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.OCCASION))
    map_dll.append(Field(FieldType.GOAL))

    # for map_dll.iternodes(): todo

    return map_dll


class TurnState:
    class PlayerTurnState(Enum):
        PLAYER_CHOOSING = 0
        PLAYER_CHOOSING_OCCASION = 1
        PLAYING_MINIGAME = 2
        DEVIL_MOVE = 3

    def __init__(self):
        self.player_id = 0
        self.player_turn_state = TurnState.PlayerTurnState.PLAYER_CHOOSING

        # This saves the remaining number of fields which will be gone, after a minigame was finished successfully
        self.remaining_move_distance = 0

    def start_minigame(self, remaining_moves):
        self.player_turn_state = TurnState.PlayerTurnState.PLAYING_MINIGAME
        self.remaining_move_distance = remaining_moves

    def choosing_occasion(self):
        self.player_turn_state = TurnState.PlayerTurnState.PLAYER_CHOOSING_OCCASION


class Game:
    def __init__(self, sio, token, host_sid, player_infos):
        self.host_sid = host_sid
        self.token = token

        # Create Evidence combination with new database connection
        DATABASES['game_init'] = db_from_env
        self.evidences = self.generate_solution_evidences()

        self.players = []
        for player_id, player_info in enumerate(player_infos):
            self.players.append(Player(player_id, player_info['name'], player_info['sid'], random.choice(self.evidences)))

        # Choose random mole
        random.choice(self.players).is_mole = True

        self.turn_state: TurnState = TurnState()

        self.map = small_map()  # small test map
        self.team_pos: dllistnode = self.map.nodeat(4)
        self.devil_pos: dllistnode = self.map.nodeat(0)

        print(self.debug_game_representation())  # test case debug

        self.move_multiplier = 1

        # TODO: Serialize Map and send with init packet
        for player in self.players:
            inv = player.inventory[0]
            print('inv:')
            print(inv)
            # evidence = {'name': inv.name, 'type': inv.evidence_type, 'subtype': inv.evidence_subtype}
            # print('evidence: {}'.format(evidence))
            sio.emit('init', {'id': player.id, 'is_mole': player.is_mole, 'map': None, 'evidence': None}, room=player.sid)

        self.send_to_all(sio, 'players_turn', {'id': self.players[0].id})

    def get_team_pos(self):
        """
        :rtype: Field
        :return: The Field the player is standing on
        """
        return self.team_pos.value

    def move_player(self, distance: int) -> int or None:
        """
        Moves the player over the map. Does not handle occasions.
        In case a minigame field is trespassed, the move is stopped and True is returned.

        :param distance: the number of fields to move
        :return: If a minigame field was reached, the number of remaining move distance is returned, otherwise None
        """
        forwards = distance >= 0
        distance = abs(distance)
        for i in range(distance):
            if forwards:
                self.team_pos = self.team_pos.next  # get next field
            else:
                self.team_pos = self.team_pos.prev  # get next field
            if self.team_pos is None:
                raise NotImplementedError('End of map reached')
            field = self.get_team_pos()
            if field.type == FieldType.MINIGAME:
                self.turn_state.player_turn_state = TurnState.PlayerTurnState.PLAYING_MINIGAME
                remaining_distance = distance - i - 1
                if not forwards:
                    remaining_distance = -remaining_distance
                return remaining_distance
        return None

    def check_end_turn(self, sio):
        if self.turn_state.player_id == len(self.players):
            self.turn_state.player_id = 0
            self.turn_state.player_turn_state = TurnState.PlayerTurnState.PLAYER_CHOOSING
            self.send_to_all(sio, 'chaser_move', random.randint(1, 6))
            self.send_to_all(sio, 'players_turn', {'id': self.get_current_player().id})

    def next_player(self, sio):
        """
        Sets turn_state.player_id to a not disabled player or to the len of players.
        Removes disabling of all players, that are skipped, because of disable.
        """
        while True:
            self.turn_state.player_id += 1
            if self.turn_state.player_id >= len(self.players):
                break
            if self.get_current_player().disabled:
                self.get_current_player().disabled = False
                print('player "{}" is not longer disabled.'.format(self.get_current_player().name))
            else:
                self.send_to_all(sio, 'players_turn', {'id': self.get_current_player().id})
                break
        self.turn_state.player_turn_state = TurnState.PlayerTurnState.PLAYER_CHOOSING

    def debug_game_representation(self):
        result = []
        for node in self.map.iternodes():  # iterate over list nodes
            field: Field = node.value
            field_text = '{}({})'.format(field.type.name, field.index)
            if node == self.team_pos:
                field_text += '+Team'
            if node == self.devil_pos:
                field_text += '+Devil'
            result.append(field_text)
            #  todo add change from numbers to characters
        return ' - '.join(result)

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
            raise InvalidUserException('Got invalid event from player "{}"'.format(player_name))

        if self.turn_state.player_turn_state != TurnState.PlayerTurnState.PLAYER_CHOOSING:
            raise InvalidUserException(
                'Got invalid player_choice message (turn_state: {})'.format(self.turn_state.player_turn_state.name)
            )

        if player_choice.get('type') == 'dice':
            move_distance = int(player_choice.get('value'))
            move_distance = (move_distance - 1) % 3 + 1
            move_distance = int(move_distance * self.move_multiplier)
            # be merciful
            if move_distance == 0:
                move_distance = 1
            self.handle_movement(sio, move_distance)
        elif player_choice.get('type') == 'share-evidence':
            pass  # TODO
        elif player_choice.get('type') == 'validate-evidence':
            pass  # TODO
        elif player_choice.get('type') == 'search-evidence':
            pass  # TODO

        self.check_end_turn(sio)

    def handle_movement(self, sio, move_distance: int):
        """
        Moves the player while handling turn state, minigames and occasions.
        """
        remaining_moves = self.move_player(move_distance)
        self.send_to_all(sio, 'move', self.get_team_pos().index)

        if remaining_moves is not None:  # minigame
            if not self.get_team_pos().type == FieldType.MINIGAME:
                raise AssertionError('got remaining moves, but not on minigame field')
            self.turn_state.start_minigame(remaining_moves)
            self.trigger_minigame()
            self.send_to_all(sio, 'minigame', 'not implemented')

            self.next_player(sio)  # TODO: remove this, if minigames are implemented
        elif self.get_team_pos().type == FieldType.OCCASION:  # check occasion field
            self.send_to_all(sio, 'occasion', {'player_id:': self.get_current_player().id})
            self.turn_state.choosing_occasion()
        else:
            self.next_player(sio)

    def player_occasion_choice(self, sio, sid, chosen_occasion: dict):
        """
        This event is called, if a player chose an occasion.

        :param chosen_occasion: A dictionary containing occasion information. Must contain a field "type", which must be
        one of: found_evidence, move_forwards, simplify_dicing, skip_player, move_backwards, hinder_dicing

        In case of move_forwards/move_backwards there should also be a "value" field containing the number of fields.
        "value" should always be positive.
        In case of skip player there should also be a "name" field, containing the name of the player
        """
        if not self.players_turn(sid):
            player = self.get_player(sid)
            player_name = '<unknown>' if player is None else player.name
            raise InvalidUserException('Got invalid event from player "{}"'.format(player_name))

        # check whether player was in turn to choose occasion
        if self.turn_state.player_turn_state != TurnState.PlayerTurnState.PLAYER_CHOOSING_OCCASION:
            raise InvalidUserException('Got player choose occasion, but player is not in turn to choose occasion')

        occasion_type = chosen_occasion.get('type')
        if occasion_type is None:
            raise InvalidMessageException('Invalid occasion choice message from client. Missing "type" in message.')
        if occasion_type == 'found_evidence':
            # TODO: add evidence and inform client(s)
            self.next_player(sio)
        elif occasion_type == 'move_forwards':
            num_fields = chosen_occasion.get('value')
            if num_fields is None:
                raise InvalidMessageException('Invalid occasion choice message from client. Missing "value" in move_forwards.')
            num_fields = int(num_fields)
            self.handle_movement(sio, num_fields)
        elif occasion_type == 'simplify_dicing':
            self.move_multiplier = 2
            self.next_player(sio)
        elif occasion_type == 'skip_player':
            player_name = chosen_occasion.get('name')
            if player_name is None:
                raise InvalidMessageException('Invalid occasion choice message from client. Missing "name" in skip_player.')
            skipped_player = self.get_player_by_name(player_name)
            if skipped_player is None:
                raise InvalidMessageException('Could not find player with name "{}"'.format(player_name))
            skipped_player.disabled = True
            self.next_player(sio)
        elif occasion_type == 'move_backwards':
            num_fields = chosen_occasion.get('value')
            if num_fields is None:
                raise InvalidMessageException('Invalid occasion choice message from client. Missing "value" in move_backwards.')
            num_fields = abs(int(num_fields))
            self.handle_movement(sio, -num_fields)
        elif occasion_type == 'hinder_dicing':
            self.move_multiplier = 0.5
            self.next_player(sio)

        self.check_end_turn(sio)

        # TODO: send more information to clients?

    def trigger_minigame(self):
        print('Minigames arent implemented yet')

    def send_to_all(self, sio, event, message=None):
        """
        Sends a message to all players in the game
        """
        if message is None:
            sio.emit(event, room=self.token)
        else:
            sio.emit(event, message, room=self.token)

    def get_current_player(self):
        return self.players[self.turn_state.player_id]

    def get_player_by_name(self, name):
        for player in self.players:
            if player.name == name:
                return player
        return None

    def players_turn(self, sid):
        return self.get_current_player().sid == sid

    def generate_solution_evidences(self):
        """
        :rtype: Evidence
        :return: List of evidences to win the game
        """
        evidences = []

        all_weapon_objects = Evidence.objects.using('game_init').filter(evidence_type=EvidenceType.WEAPON,
                                                     evidence_subtype=EvidenceSubtype.OBJECT).values_list()
        all_weapon_colors = Evidence.objects.using('game_init').filter(evidence_type=EvidenceType.WEAPON,
                                                    evidence_subtype=EvidenceSubtype.COLOR).values_list()
        all_weapon_conditions = Evidence.objects.using('game_init').filter(evidence_type=EvidenceType.WEAPON,
                                                        evidence_subtype=EvidenceSubtype.CONDITION).values_list()
        evidences.append(random.choice(all_weapon_objects))
        evidences.append(random.choice(all_weapon_colors))
        evidences.append(random.choice(all_weapon_conditions))

        all_crime_scene_locations = Evidence.objects.using('game_init').filter(evidence_type=EvidenceType.CRIME_SCENE,
                                                            evidence_subtype=EvidenceSubtype.LOCATION).values_list()
        all_crime_scene_temperature = Evidence.objects.using('game_init').filter(evidence_type=EvidenceType.CRIME_SCENE,
                                                              evidence_subtype=EvidenceSubtype.TEMPERATURE).values_list()
        all_crime_scene_districts = Evidence.objects.using('game_init').filter(evidence_type=EvidenceType.CRIME_SCENE,
                                                            evidence_subtype=EvidenceSubtype.DISTRICT).values_list()
        evidences.append(random.choice(all_crime_scene_locations))
        evidences.append(random.choice(all_crime_scene_temperature))
        evidences.append(random.choice(all_crime_scene_districts))

        all_offender_escape_clothings = Evidence.objects.using('game_init').filter(evidence_type=EvidenceType.OFFENDER,
                                                                evidence_subtype=EvidenceSubtype.CLOTHING).values_list()
        all_offender_escape_sizes = Evidence.objects.using('game_init').filter(evidence_type=EvidenceType.OFFENDER,
                                                            evidence_subtype=EvidenceSubtype.SIZE).values_list()
        all_offender_escape_characteristics = Evidence.objects.using('game_init').filter(evidence_type=EvidenceType.OFFENDER,
                                                                      evidence_subtype=EvidenceSubtype.CHARACTERISTIC).values_list()
        evidences.append(random.choice(all_offender_escape_clothings))
        evidences.append(random.choice(all_offender_escape_sizes))
        evidences.append(random.choice(all_offender_escape_characteristics))

        all_time_of_crime_weekdays = Evidence.objects.using('game_init').filter(evidence_type=EvidenceType.TIME_OF_CRIME,
                                                             evidence_subtype=EvidenceSubtype.WEEKDAY).values_list()
        all_time_of_crime_daytimes = Evidence.objects.using('game_init').filter(evidence_type=EvidenceType.TIME_OF_CRIME,
                                                             evidence_subtype=EvidenceSubtype.DAYTIME).values_list()
        all_time_of_crime_times = Evidence.objects.using('game_init').filter(evidence_type=EvidenceType.TIME_OF_CRIME,
                                                          evidence_subtype=EvidenceSubtype.TIME).values_list()
        evidences.append(random.choice(all_time_of_crime_weekdays))
        evidences.append(random.choice(all_time_of_crime_daytimes))
        evidences.append(random.choice(all_time_of_crime_times))

        all_mean_of_escape_conditions = Evidence.objects.using('game_init').filter(evidence_type=EvidenceType.MEANS_OF_ESCAPE,
                                                                evidence_subtype=EvidenceSubtype.MODEL).values_list()
        all_mean_of_escape_daytime = Evidence.objects.using('game_init').filter(evidence_type=EvidenceType.MEANS_OF_ESCAPE,
                                                             evidence_subtype=EvidenceSubtype.COLOR).values_list()
        all_mean_of_escape_districts = Evidence.objects.using('game_init').filter(evidence_type=EvidenceType.MEANS_OF_ESCAPE,
                                                               evidence_subtype=EvidenceSubtype.ESCAPE_ROUTE).values_list()
        evidences.append(random.choice(all_mean_of_escape_conditions))
        evidences.append(random.choice(all_mean_of_escape_daytime))
        evidences.append(random.choice(all_mean_of_escape_districts))

        return evidences


class FieldType(Enum):
    WALKABLE = 1
    OCCASION = 2
    MINIGAME = 3
    DEVIL_FIELD = 4
    SHORTCUT = 5
    GOAL = 6


class Field:
    counter = 0

    def __init__(self, field_type=FieldType.WALKABLE, shortcut_field=None):
        self.index = Field.counter
        Field.counter = Field.counter + 1
        self.shortcut_field = shortcut_field    # type: dllist
        self.type = field_type                  # type: FieldType


class InvalidUserException(Exception):
    pass


class InvalidMessageException(Exception):
    pass
