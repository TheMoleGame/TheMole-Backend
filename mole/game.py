import time
from enum import Enum
import random

from .models import Evidence, ClueType, ClueSubtype
import pyllist
import dj_database_url
from .game_character import *
from mole_backend.settings import DATABASES


OCCASIONS = ['found_clue', 'move_forwards', 'simplify_dicing', 'skip_player', 'hinder_dicing']

random.seed(time.time())


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
        self.player_turn_state = TurnState.PlayerTurnState.GAME_OVER
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

        self.clues = self.generate_solution_clues()
        self.team_proofs = []
        self.mole_proofs = []

        self.players = []
        for player_id, player_info in enumerate(player_infos):
            self.players.append(Player(player_id, player_info['name'], player_info['sid'], random.choice(self.clues)))

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
            clue = {'name': inv[1], 'type': inv[2], 'subtype': inv[3]}
            print('clue: {}'.format(clue))
            sio.emit('init', {'player_id': player.player_id, 'is_mole': player.is_mole, 'map': None, 'clue': clue}, room=player.sid)

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
            # set player_index to first not disabled player
            self.turn_state.player_index = 0
            while self.get_current_player().disabled:
                self.get_current_player().disabled = False
                print('player "{}" is not longer disabled.'.format(self.get_current_player().name))
                self.turn_state.player_index += 1

                # This only happens, when all players are disabled in a round...
                if self.turn_state.player_index == len(self.players):
                    self.turn_state.player_index = 0
                    self.follower_move(sio)  # in this case the follower moves two times
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

         - sharing clue:
            player_choice is in the following form:
            {
                'type': 'share-clue',
                'with': player_name,
                'clue': clue_name,
            }

         - validating clue:
            player_choice is in the following form:
            {
                'type': 'validate-clue',
                'clues': [clue_name1, clue_name2, ...],
            }

         - searches for clue:
            player_choice is in the following form:
            {
                'type': 'search-clue',
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

        # TODO: Eventuell player_id und clue_id (oder type + subtype) übergeben, anstatt name!
        elif player_choice.get('type') == 'share-clue':
            player = self.get_player(sid)
            print('share-clue')
            # Get player with whom the clue should be shared
            share_with = next((player for player in self.players if player.name == player_choice.get('with')), None)
            if share_with is None:
                raise InvalidUserException('Got invalid player name (with: {})'.format(player_choice.get('with')))

            # Get clue which should be shared
            share_clue = next((clue for clue in player.inventory if clue[1] == player_choice.get('clue')), None)
            if share_clue is None:
                raise InvalidUserException('Got invalid clue name (clue: {})'.format(player_choice.get('clue')))
            share_with.inventory.append(share_clue)

            # Share clue with player
            share_clue = {'name': share_clue[1], 'type': share_clue[2], 'subtype': share_clue[3]}
            sio.emit(
                'receive_clue',
                {'from:': player.player_id, 'clue': share_clue},
                room=share_with.sid
            )

            self.next_player(sio)

        elif player_choice.get('type') == 'validate-clues':
            player = self.get_player(sid)
            clues = player_choice.get('clues')
            successful_validation = self.validate_clues(clues)

            if successful_validation:
                self.add_verified_clues_to_proofs(clues, player.is_mole)
                self.send_to_all(player.sid, 'validation_result', {'successful_validation': successful_validation})
            else:
                sio.emit(
                    'validation_result',
                    {'successful_validation': successful_validation},
                    room=player.sid
                )

            self.next_player(sio)

        elif player_choice.get('type') == 'search-clue':
            player = self.get_player(sid)
            clue = None

            if player_choice.get('success') is True:
                clue = self.get_random_missing_clue(player.inventory)
                player.inventory.append(clue)
                clue = {'name': clue[1], 'type': clue[2], 'subtype': clue[3]}

            sio.emit(
                'receive_clue',
                {'from:': -1, 'clue': clue},
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
            if self.get_team_pos().type not in [FieldType.MINIGAME, FieldType.SHORTCUT]:
                raise AssertionError(
                    'got remaining moves, but not on minigame field.\ncurrent field type: {}'.format(
                        self.get_team_pos().type.name
                    )
                )
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
        one of: found_clue, move_forwards, simplify_dicing, skip_player, hinder_dicing

        In case of move_forwards there should also be a "value" field containing the number of fields.
        "value" should always be positive.
        In case of skip player there should also be a "name" field, containing the name of the player
        In case of found clue there should also be a "success" field, containing a Bool.
        """
        print(
            'got player occasion choice: {}\npossible occasions: {}'.format(
                chosen_occasion,
                self.turn_state.occasion_choices
            )
        )
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

        if occasion_type == 'found_clue':
            player = self.get_player(sid)
            clue = None

            if chosen_occasion.get('success') is True:
                clue = self.get_random_missing_clue(player.inventory)
                player.inventory.append(clue)
                clue = {'name': clue[1], 'type': clue[2], 'subtype': clue[3]}

            sio.emit(
                'receive_clue',
                {'from:': -1, 'clue': clue},
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


    def get_random_missing_clue(self, clues):
        """
        :rtype: Evidence
        :return: Get a random clue, which the player does not have yet
        """
        missing_clues = []

        for clue in self.clues:
            c = next((c for c in clues if c[1] != clue[1]), None)

            if c is not None:
                missing_clues.append(clue)
                break

        print("missing clues: {}".format(missing_clues))
        return random.choice(missing_clues)


    def validate_clues(self, clues):
        """
        :rtype: Bool
        :return: Bool whether the correct clues were found or not
        """
        print('clues[0]: {}'.format(clues[0]))
        # TODO: this seems to crash, when reaching end of game. Tuple indices must be integers or slices, not str
        clue_type = clues[0]['type']
        clue_group = []

        # Get all winner clues with requested clue type
        for clue in self.clues:
            if clue[2] == clue_type:
                clue_group.append(clue)

        # Check if player has all the clues needed
        for clue in clues:
            if clue['type'] != clue_type:
                return False

            result = next((e for e in clue_group if e[1] == clue['name']), None)
            if result is not None:
                clue_group.remove(result)

        return len(clue_group) == 0


    def add_verified_clues_to_proofs(self, clues, is_mole):
        # Check if the verified clues have already been added to the proofs, otherwise add them to the correct proof list
        for clue in clues:
            if is_mole is True and next((c for c in self.mole_proofs if c['name'] == clue['name']), None) is None:
                self.mole_proofs.append(clue)
            elif is_mole is False and next((c for c in self.team_proofs if c['name'] == clue['name']), None) is None:
                self.team_proofs.append(clue)


    def generate_solution_clues(self):
        """
        :rtype: list[Evidence]
        :return: List of clues to win the game
        """
        clues = []
        db_connection = 'game_init{}'.format(self.token)

        all_weapon_objects = Evidence.objects.using(db_connection).filter(type=ClueType.WEAPON,
                                                                          subtype=ClueSubtype.OBJECT).values_list()
        all_weapon_colors = Evidence.objects.using(db_connection).filter(type=ClueType.WEAPON,
                                                                         subtype=ClueSubtype.COLOR).values_list()
        all_weapon_conditions = Evidence.objects.using(db_connection).filter(type=ClueType.WEAPON,
                                                                             subtype=ClueSubtype.CONDITION).values_list()
        clues.append(random.choice(all_weapon_objects))
        clues.append(random.choice(all_weapon_colors))
        clues.append(random.choice(all_weapon_conditions))

        all_crime_scene_locations = Evidence.objects.using(db_connection).filter(type=ClueType.CRIME_SCENE,
                                                                                 subtype=ClueSubtype.LOCATION).values_list()
        all_crime_scene_temperature = Evidence.objects.using(db_connection).filter(type=ClueType.CRIME_SCENE,
                                                                                   subtype=ClueSubtype.TEMPERATURE).values_list()
        all_crime_scene_districts = Evidence.objects.using(db_connection).filter(type=ClueType.CRIME_SCENE,
                                                                                 subtype=ClueSubtype.DISTRICT).values_list()
        clues.append(random.choice(all_crime_scene_locations))
        clues.append(random.choice(all_crime_scene_temperature))
        clues.append(random.choice(all_crime_scene_districts))

        all_offender_escape_clothings = Evidence.objects.using(db_connection).filter(type=ClueType.OFFENDER,
                                                                                     subtype=ClueSubtype.CLOTHING).values_list()
        all_offender_escape_sizes = Evidence.objects.using(db_connection).filter(type=ClueType.OFFENDER,
                                                                                 subtype=ClueSubtype.SIZE).values_list()
        all_offender_escape_characteristics = Evidence.objects.using(db_connection).filter(type=ClueType.OFFENDER,
                                                                                           subtype=ClueSubtype.CHARACTERISTIC).values_list()
        clues.append(random.choice(all_offender_escape_clothings))
        clues.append(random.choice(all_offender_escape_sizes))
        clues.append(random.choice(all_offender_escape_characteristics))

        all_time_of_crime_weekdays = Evidence.objects.using(db_connection).filter(type=ClueType.TIME_OF_CRIME,
                                                                                  subtype=ClueSubtype.WEEKDAY).values_list()
        all_time_of_crime_daytimes = Evidence.objects.using(db_connection).filter(type=ClueType.TIME_OF_CRIME,
                                                                                  subtype=ClueSubtype.DAYTIME).values_list()
        all_time_of_crime_times = Evidence.objects.using(db_connection).filter(type=ClueType.TIME_OF_CRIME,
                                                                               subtype=ClueSubtype.TIME).values_list()
        clues.append(random.choice(all_time_of_crime_weekdays))
        clues.append(random.choice(all_time_of_crime_daytimes))
        clues.append(random.choice(all_time_of_crime_times))

        all_mean_of_escape_conditions = Evidence.objects.using(db_connection).filter(type=ClueType.MEANS_OF_ESCAPE,
                                                                                     subtype=ClueSubtype.MODEL).values_list()
        all_mean_of_escape_daytime = Evidence.objects.using(db_connection).filter(type=ClueType.MEANS_OF_ESCAPE,
                                                                                  subtype=ClueSubtype.COLOR).values_list()
        all_mean_of_escape_districts = Evidence.objects.using(db_connection).filter(type=ClueType.MEANS_OF_ESCAPE,
                                                                                    subtype=ClueSubtype.ESCAPE_ROUTE).values_list()
        clues.append(random.choice(all_mean_of_escape_conditions))
        clues.append(random.choice(all_mean_of_escape_daytime))
        clues.append(random.choice(all_mean_of_escape_districts))

        return clues

    def game_over(self):
        self.turn_state.game_over()
        # if mole player won
        # let everybody guess one last time?
        # check if any players clues match the goal clues
        result = "Mole wins"
        for player in self.players:
            if self.validate_clues(player.inventory):
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

    map_dll.append(Field(FieldType.WALKABLE))  # team - [4] fifth
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.OCCASION))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.OCCASION))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.MINIGAME))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.OCCASION))
    map_dll.append(Field(FieldType.OCCASION))
    map_dll.append(Field(FieldType.SHORTCUT, 18))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.MINIGAME))
    map_dll.append(Field(FieldType.OCCASION))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.Goal))

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
    map_dll.append(Field(FieldType.SHORTCUT, 18))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.OCCASION))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.MINIGAME))
    map_dll.append(Field(FieldType.OCCASION))
    map_dll.append(Field(FieldType.WALKABLE))
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
#   map_dll.append(Field(FieldType.WALKABLE, True))
#   map_dll.append(Field(FieldType.WALKABLE, True))
#   map_dll.append(Field(FieldType.WALKABLE, 32))
#   # Shortcut 2
#   map_dll.append(Field(FieldType.WALKABLE, True))
#   map_dll.append(Field(FieldType.WALKABLE, True))
#   map_dll.append(Field(FieldType.WALKABLE, True))
#   map_dll.append(Field(FieldType.WALKABLE, 45))
#   # Shortcut 3
#   map_dll.append(Field(FieldType.WALKABLE, True))
#   map_dll.append(Field(FieldType.WALKABLE, True))
#   map_dll.append(Field(FieldType.WALKABLE, True))
#   map_dll.append(Field(FieldType.WALKABLE, 57))

    return map_dll
