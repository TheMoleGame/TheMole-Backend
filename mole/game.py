from enum import Enum
import random

from .models import Evidence, EvidenceType, EvidenceSubtype
import pyllist
import dj_database_url
from .game_character import *
from mole_backend.settings import DATABASES


OCCASIONS = ['found_evidence', 'move_forwards', 'simplify_dicing', 'skip_player', 'hinder_dicing']


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

        # This saves the remaining number of fields which will be gone, after a minigame was finished successfully
        self.remaining_move_distance = 0

    def start_minigame(self, remaining_moves):
        self.player_turn_state = TurnState.PlayerTurnState.PLAYING_MINIGAME
        self.remaining_move_distance = remaining_moves

    def choosing_occasion(self, occasion_choices):
        self.player_turn_state = TurnState.PlayerTurnState.PLAYER_CHOOSING_OCCASION
        self.occasion_choices = occasion_choices

    def game_over(self):
        self.player_turn_state = TurnState.PlayerTurnState.Game_Over
        self.occasion_choices = None

    def to_dict(self):
        return {
            'player_index': self.player_index,
            'player_turn_state': self.player_turn_state.name,
            'occasion_choices': self.occasion_choices,
            'remaining_move_distance': self.remaining_move_distance,
        }


def _random_occasion_choices():
    choices = random.sample(OCCASIONS, 2)

    def _enrich_choice(choice):
        result = {'type': choice}
        if choice == 'move_forwards':
            result['value'] = random.randint(1, 4)
        elif choice == 'skip_player':
            result['name'] = None
        return result

    return list(map(_enrich_choice, choices))


class Game:
    def __init__(self, sio, token, host_sid, player_infos):
        self.host_sid = host_sid
        self.token = token
        self.sio = sio
        # Create Evidence combination with new database connection
        DATABASES['game_init{}'.format(self.token)] = dj_database_url.config(conn_max_age=600)

        self.evidences = self.generate_solution_evidences()

        self.players = []
        for player_id, player_info in enumerate(player_infos):
            self.players.append(Player(player_id, player_info['name'], player_info['sid'], random.choice(self.evidences)))

        # Choose random mole
        random.choice(self.players).is_mole = True

        self.turn_state: TurnState = TurnState()

        self.map = small_map_shortcut()  # small test map
        self.team_pos: pyllist.dllistnode = self.map.nodeat(4)
        self.follower_pos: pyllist.dllistnode = self.map.nodeat(0)
        self.debug_game_representation()  # test case debug

        # print(self.map_to_json())
        # self.move(2, self.players[0])  # test case move

        self.move_multiplier = 1

        # TODO: Serialize Map and send with init packet
        for player in self.players:
            inv = player.inventory[0]
            evidence = {'name': inv[1], 'type': inv[2], 'subtype': inv[3]}
            print('evidence: {}'.format(evidence))
            sio.emit('init', {'player_id': player.player_id, 'is_mole': player.is_mole, 'map': None, 'evidence': evidence}, room=player.sid)

        self.send_to_all(sio, 'players_turn', {'player_id': self.players[0].player_id})

    def _get_player_info(self):
        return list(map(lambda p: {'player_id': p.player_id, 'name': p.name}, self.players))

    def get_team_pos(self):
        """
        :rtype: Field
        :return: The Field the player is standing on
        """
        return self.team_pos.value

    def get_follower_pos(self):
        """
        :rtype: Field
        :return: The Field the devil is standing on
        """
        return self.follower_pos.value

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
                self.game_over()  # raise NotImplementedError('End of map reached')
            else:
                field = self.get_team_pos()
                if field.type == FieldType.MINIGAME:
                    self.turn_state.player_turn_state = TurnState.PlayerTurnState.PLAYING_MINIGAME
                    remaining_distance = distance - i - 1
                    if not forwards:
                        remaining_distance = -remaining_distance
                    return remaining_distance
        return None

    def check_end_turn(self, sio):
        if self.turn_state.player_index == len(self.players):
            self.turn_state.player_index = 0
            self.turn_state.player_turn_state = TurnState.PlayerTurnState.PLAYER_CHOOSING
            self.follower_move(sio)
            self.send_to_all(sio, 'players_turn', {'player_id': self.get_current_player().player_id})

    def follower_move(self, sio):
        num_fields = random.randint(1, 6)
        for i in range(num_fields):
            self.follower_pos = self.follower_pos.next
            if self.follower_pos is None:
                raise Exception('Follower reached end of map')  # TODO
            if self.get_follower_pos().index == self.get_team_pos().index:
                raise Exception('Follower caught players')  # TODO

        self.send_to_all(sio, 'follower_move', self.get_follower_pos().index)

    def next_player(self, sio):
        """
        Sets turn_state.player_id to a not disabled player or to the len of players.
        Removes disabling of all players, that are skipped, because of disable.
        """
        while True:
            self.turn_state.player_index += 1
            if self.turn_state.player_index >= len(self.players):
                break
            if self.get_current_player().disabled:
                self.get_current_player().disabled = False
                print('player "{}" is not longer disabled.'.format(self.get_current_player().name))
            else:
                self.send_to_all(sio, 'players_turn', {'player_id': self.get_current_player().player_id})
                break
        self.turn_state.player_turn_state = TurnState.PlayerTurnState.PLAYER_CHOOSING

    def debug_game_representation(self):
        result = ""
        print('-------------Game-Representation---------------------')
        print('-----------------------------------------------------')
        print('Player ' + str(self.get_current_player().name)+'s turn')
        for node in self.map.iternodes():  # iterate over list nodes
            field: Field = node.value
            result += ' - '+str(field.type.name)
            if node == self.team_pos:
                result += '+Team'
            if node == self.follower_pos:
                result += '+ Devil'
        print(result)
        print('---------------------------------------------------')
        print('---------------------------------------------------')

    def map_to_json(self):
        json_map = list()
        for node in self.map.iternodes():  # iterate over list nodes
            field: Field = node.value
            json_map.append(field)

        return json_map

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
            raise InvalidUserException(
                'Got invalid event from player "{}".\nturn state: {}\nplayer event: {}'.format(
                    player_name,
                    self.turn_state.to_dict(),
                    player_choice
                )
            )

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

        # TODO: Eventuell player_id und evidence_id (oder type + subtype) übergeben, anstatt name!
        elif player_choice.get('type') == 'share-evidence':
            player = self.get_player(sid)

            # Get player with whom the evidence should be shared
            share_with = next((player for player in self.players if player.name == player_choice.get('with')), None)
            if share_with is None:
                raise InvalidUserException('Got invalid player name (with: {})'.format(player_choice.get('with')))

            # Get evidence which should be shared
            share_evidence = next((evidence for evidence in player.inventory if evidence[1] == player_choice.get('evidence')), None)
            if share_evidence is None:
                raise InvalidUserException('Got invalid evidence name (evidence: {})'.format(player_choice.get('evidence')))
            share_with.inventory.append(share_evidence)

            # Share evidence with player
            share_evidence = {'name': share_evidence[1], 'type': share_evidence[2], 'subtype': share_evidence[3]}
            sio.emit(
                'receive_evidence',
                {'from:': player.player_id, 'evidence': share_evidence},
                room=share_with.sid
            )
            self.next_player(sio)

        elif player_choice.get('type') == 'validate-evidence':
            player = self.get_player(sid)
            successful_validation = self.validate_evidence(player_choice.get('evidences'))

            sio.emit(
                'validation_result',
                {'successful_validation': successful_validation},
                room=player.sid
            )

            self.next_player(sio)
        elif player_choice.get('type') == 'search-evidence':
            player = self.get_player(sid)
            evidence = None

            # Probability of 25 percent
            if random.random() < 0.25:
                # Check what evidence the player does not have yet
                missing_evidences = []
                for evidence1 in player.inventory:
                    for evidence2 in self.evidences:
                        if evidence1[0] == evidence2[0]:
                            missing_evidences.append(evidence1)
                            break

                evidence = random.choice(missing_evidences)
                player.inventory.append(evidence)
                evidence = {'name': evidence[1], 'type': evidence[2], 'subtype': evidence[3]}

            sio.emit(
                'receive_evidence',
                {'from:': -1, 'evidence': evidence},
                room=player.sid
            )

            self.next_player(sio)

        self.check_end_turn(sio)

    def handle_movement(self, sio, move_distance: int):
        """
        Moves the player while handling turn state, minigames and occasions.
        """
        remaining_moves = self.move_player(move_distance)
        self.send_to_all(sio, 'move', self.get_team_pos().index)

        # TODO remove second condition (self.get_team_pos().type == FieldType.SHORTCUT) to make shortcut fields possible
        if remaining_moves is not None or self.get_team_pos().type == FieldType.SHORTCUT:
            print("stepped on minigame")
            if not self.get_team_pos().type == FieldType.MINIGAME:
                raise AssertionError('got remaining moves, but not on minigame field')
            self.turn_state.start_minigame(remaining_moves)
            self.trigger_minigame()
            self.send_to_all(sio, 'minigame', 'not implemented')

            self.next_player(sio)  # TODO: remove this, if minigames are implemented
        elif self.get_team_pos().type == FieldType.OCCASION:  # check occasion field
            print("stepped on occasion")
            occasion_choices = _random_occasion_choices()
            for player in self.players:
                if self.get_current_player().sid == player.sid:
                    sio.emit(
                        'occasion',
                        {'player_id:': self.get_current_player().player_id, 'choices': occasion_choices},
                        room=player.sid
                    )
                else:
                    sio.emit(
                        'occasion',
                        {'player_id:': self.get_current_player().player_id},
                        room=player.sid
                    )
            self.turn_state.choosing_occasion(occasion_choices)
        elif self.get_team_pos().type == FieldType.SHORTCUT:  # TODO: this is currently unreachable. See first condition
            print("stepped on minigame field")
            # todo
            # if minigame was won
            self.team_pos = self.map.nodeat(self.get_team_pos().shortcut_field)
            # if minigame was lost
            # do nothing stay at spot or walk remaining moves
        elif self.get_team_pos().type == FieldType.Goal:
            print("stepped on goal field")
            self.game_over()
        else:
            print("stepped on normal field")
            self.next_player(sio)

    def player_occasion_choice(self, sio, sid, chosen_occasion: dict):
        """
        This event is called, if a player chose an occasion.

        :param chosen_occasion: A dictionary containing occasion information. Must contain a field "type", which must be
        one of: found_evidence, move_forwards, simplify_dicing, skip_player, hinder_dicing

        In case of move_forwards there should also be a "value" field containing the number of fields.
        "value" should always be positive.
        In case of skip player there should also be a "name" field, containing the name of the player
        """
        print("player choosing occasion")
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

        if not any(map(lambda oc: _occasion_matches(chosen_occasion, oc), self.turn_state.occasion_choices)):
            raise InvalidMessageException(
                'Invalid occasion choice message from client. chosen_occasion does not match any in occasion choices:\n'
                'possible occasion choices: {}\n'
                'occasion choice: {}'.format(self.turn_state.occasion_choices, chosen_occasion)
            )

        if occasion_type == 'found_evidence':
            evidence = random.choice(self.evidences)
            player = self.get_player(sid)
            player.inventory.append(evidence)

            evidence = {'name': evidence[1], 'type': evidence[2], 'subtype': evidence[3]}
            sio.emit(
                'receive_evidence',
                {'from:': -1, 'evidence': evidence},
                room=player.sid
            )
            self.next_player(sio)

        elif occasion_type == 'move_forwards':
            num_fields = chosen_occasion.get('value')
            if num_fields is None:
                raise InvalidMessageException(
                    'Invalid occasion choice message from client. Missing "value" in move_forwards.'
                )
            num_fields = int(num_fields)
            self.handle_movement(sio, num_fields)
        elif occasion_type == 'simplify_dicing':
            self.move_multiplier = 2
            self.next_player(sio)
        elif occasion_type == 'skip_player':
            player_name = chosen_occasion.get('name')
            if player_name is None:
                raise InvalidMessageException(
                    'Invalid occasion choice message from client. Missing "name" in skip_player.'
                )
            skipped_player = self.get_player_by_name(player_name)
            if skipped_player is None:
                raise InvalidMessageException('Could not find player with name "{}"'.format(player_name))
            skipped_player.disabled = True
            self.next_player(sio)
        elif occasion_type == 'hinder_dicing':
            self.move_multiplier = 0.5
            self.next_player(sio)

        self.check_end_turn(sio)

        self.turn_state.occasion_choices = None  # reset occasion choices

    # noinspection PyMethodMayBeStatic
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
        return self.players[self.turn_state.player_index]

    def get_player_by_name(self, name):
        for player in self.players:
            if player.name == name:
                return player
        return None

    def players_turn(self, sid):
        return self.get_current_player().sid == sid

    def validate_evidence(self, evidences):
        """
        :rtype: Evidence
        :return: Bool
        """
        evidence_type = evidences[0]['type']
        evidence_group = []

        # Get all winner evidences with requested evidence type
        for evidence in self.evidences:
            if evidence[2] == evidence_type:
                evidence_group.append(evidence)

        # Check if player has all the evidences needed
        for evidence in evidences:
            if evidence['type'] != evidence_type:
                return False

            result = next((e for e in evidence_group if e[1] == evidence['name']), None)
            if result is not None:
                evidence_group.remove(result)

        return len(evidence_group) == 0

    def generate_solution_evidences(self):
        """
        :rtype: Evidence
        :return: List of evidences to win the game
        """
        evidences = []
        db_connection = 'game_init{}'.format(self.token)

        all_weapon_objects = Evidence.objects.using(db_connection).filter(type=EvidenceType.WEAPON,
                                                                        subtype=EvidenceSubtype.OBJECT).values_list()
        all_weapon_colors = Evidence.objects.using(db_connection).filter(type=EvidenceType.WEAPON,
                                                    subtype=EvidenceSubtype.COLOR).values_list()
        all_weapon_conditions = Evidence.objects.using(db_connection).filter(type=EvidenceType.WEAPON,
                                                        subtype=EvidenceSubtype.CONDITION).values_list()
        evidences.append(random.choice(all_weapon_objects))
        evidences.append(random.choice(all_weapon_colors))
        evidences.append(random.choice(all_weapon_conditions))

        all_crime_scene_locations = Evidence.objects.using(db_connection).filter(type=EvidenceType.CRIME_SCENE,
                                                            subtype=EvidenceSubtype.LOCATION).values_list()
        all_crime_scene_temperature = Evidence.objects.using(db_connection).filter(type=EvidenceType.CRIME_SCENE,
                                                              subtype=EvidenceSubtype.TEMPERATURE).values_list()
        all_crime_scene_districts = Evidence.objects.using(db_connection).filter(type=EvidenceType.CRIME_SCENE,
                                                            subtype=EvidenceSubtype.DISTRICT).values_list()
        evidences.append(random.choice(all_crime_scene_locations))
        evidences.append(random.choice(all_crime_scene_temperature))
        evidences.append(random.choice(all_crime_scene_districts))

        all_offender_escape_clothings = Evidence.objects.using(db_connection).filter(type=EvidenceType.OFFENDER,
                                                                subtype=EvidenceSubtype.CLOTHING).values_list()
        all_offender_escape_sizes = Evidence.objects.using(db_connection).filter(type=EvidenceType.OFFENDER,
                                                            subtype=EvidenceSubtype.SIZE).values_list()
        all_offender_escape_characteristics = Evidence.objects.using(db_connection).filter(type=EvidenceType.OFFENDER,
                                                                      subtype=EvidenceSubtype.CHARACTERISTIC).values_list()
        evidences.append(random.choice(all_offender_escape_clothings))
        evidences.append(random.choice(all_offender_escape_sizes))
        evidences.append(random.choice(all_offender_escape_characteristics))

        all_time_of_crime_weekdays = Evidence.objects.using(db_connection).filter(type=EvidenceType.TIME_OF_CRIME,
                                                             subtype=EvidenceSubtype.WEEKDAY).values_list()
        all_time_of_crime_daytimes = Evidence.objects.using(db_connection).filter(type=EvidenceType.TIME_OF_CRIME,
                                                             subtype=EvidenceSubtype.DAYTIME).values_list()
        all_time_of_crime_times = Evidence.objects.using(db_connection).filter(type=EvidenceType.TIME_OF_CRIME,
                                                          subtype=EvidenceSubtype.TIME).values_list()
        evidences.append(random.choice(all_time_of_crime_weekdays))
        evidences.append(random.choice(all_time_of_crime_daytimes))
        evidences.append(random.choice(all_time_of_crime_times))

        all_mean_of_escape_conditions = Evidence.objects.using(db_connection).filter(type=EvidenceType.MEANS_OF_ESCAPE,
                                                                subtype=EvidenceSubtype.MODEL).values_list()
        all_mean_of_escape_daytime = Evidence.objects.using(db_connection).filter(type=EvidenceType.MEANS_OF_ESCAPE,
                                                             subtype=EvidenceSubtype.COLOR).values_list()
        all_mean_of_escape_districts = Evidence.objects.using(db_connection).filter(type=EvidenceType.MEANS_OF_ESCAPE,
                                                               subtype=EvidenceSubtype.ESCAPE_ROUTE).values_list()
        evidences.append(random.choice(all_mean_of_escape_conditions))
        evidences.append(random.choice(all_mean_of_escape_daytime))
        evidences.append(random.choice(all_mean_of_escape_districts))

        return evidences

    def game_over(self):
        self.turn_state.game_over()
        # if mole player won
        # let everybody guess one last time?
        # check if any players evidences match the goal evidences
        result = "Mole wins"
        for player in self.players:
            if self.validate_evidence(player.inventory):
                result = "Team wins"
                break
        print('---------------------------------------------\n' +
              '--------------GAME OVER----------------------\n' +
              '---------------------------------------------\n' +
              '----------------'+result+'------------------------')
        self.send_to_all(self.sio, 'gameover', result)


def _occasion_matches(left, right):
    if left['type'] != right['type']:
        return False
    if left['type'] == 'move_forwards':
        if left['value'] != right['value']:
            return False
    return True


class FieldType(str, Enum):
    WALKABLE = 'walkable'
    OCCASION = 'occasion'
    MINIGAME = 'minigame'
    DEVIL_FIELD = 'devil_field'
    SHORTCUT = 'shortcut'
    Goal = 'goal'


class Field(dict):
    counter = 0

    def __init__(self, field_type=FieldType.WALKABLE, shortcut_field=None):
        dict.__init__(self, index=Field.counter)
        self.index = Field.counter
        Field.counter = Field.counter + 1
        self.shortcut_field = shortcut_field    # type: pyllist.dllist
        self.type = field_type                  # type: FieldType
        dict.__setitem__(self, "shortcut", self.shortcut_field)
        dict.__setitem__(self, "field_type", self.type)


class InvalidUserException(Exception):
    pass


class InvalidMessageException(Exception):
    pass


def small_map_shortcut():
    # reset counter
    Field.counter = 0

    map_dll = pyllist.dllist()  # double linked List
    #  First Field
    init_f = Field(FieldType.DEVIL_FIELD)  # devil should start here
    map_dll.append(init_f)
    for i in range(0, 3):
        map_dll.append(Field(FieldType.DEVIL_FIELD))

    map_dll.append(Field(FieldType.WALKABLE))  # Team should be here
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.OCCASION))
    short = Field(FieldType.SHORTCUT, 12)  #
    map_dll.append(short)
    map_dll.append(Field(FieldType.OCCASION))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.MINIGAME))
    map_dll.append(Field(FieldType.Goal))

#    shortcut
    map_dll.append(Field(FieldType.WALKABLE, True))
    map_dll.append(Field(FieldType.WALKABLE, True))
    map_dll.append(Field(FieldType.SHORTCUT, 10))

    return map_dll


def create_big_map():
    # reset counter
    Field.counter = 0

    map_dll = pyllist.dllist()  # double linked List
    #  First Field
    init_f = Field(FieldType.DEVIL_FIELD)  # devil
    map_dll.append(init_f)

    for i in range(0, 3):
        map_dll.append(Field(FieldType.DEVIL_FIELD))

    map_dll.append(Field(FieldType.WALKABLE))  # team - id=4
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
    map_dll.append(Field(FieldType.SHORTCUT, 40))  # 25

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
    map_dll.append(Field(FieldType.SHORTCUT, 66))
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
    map_dll.append(Field(FieldType.SHORTCUT, 70))  # 52
    map_dll.append(Field(FieldType.OCCASION))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.OCCASION))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.OCCASION))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.OCCASION))
    map_dll.append(Field(FieldType.Goal))  # id=62 ?

    # Shortcut
    map_dll.append(Field(FieldType.WALKABLE, True))
    map_dll.append(Field(FieldType.WALKABLE, True))
    map_dll.append(Field(FieldType.WALKABLE, 32))
    # Shortcut 2
    map_dll.append(Field(FieldType.WALKABLE, True))
    map_dll.append(Field(FieldType.WALKABLE, True))
    map_dll.append(Field(FieldType.WALKABLE, True))
    map_dll.append(Field(FieldType.WALKABLE, 45))
    # Shortcut 3
    map_dll.append(Field(FieldType.WALKABLE, True))
    map_dll.append(Field(FieldType.WALKABLE, True))
    map_dll.append(Field(FieldType.WALKABLE, True))
    map_dll.append(Field(FieldType.WALKABLE, 57))

    return map_dll
