# -*- coding: utf-8 -*-
import sys
import time
from copy import deepcopy
from enum import Enum
import random
import pyllist
import dj_database_url

from .models import Evidence, ClueType, ClueSubtype
from .game_character import *
from mole_backend.settings import DATABASES


OCCASIONS = ['found_clue', 'move_forwards', 'simplify_dicing', 'skip_player', 'hinder_dicing']
DEFAULT_START_POSITION = 4

random.seed(time.time())


class MoveModifier(Enum):
    NORMAL = 0
    HINDER = 1
    SIMPLIFY = 2

    def get_factor(self):
        if self == MoveModifier.NORMAL:
            return 1.0
        elif self == MoveModifier.HINDER:
            return 0.5
        elif self == MoveModifier.SIMPLIFY:
            return 2.0
        else:
            raise Exception('move modifier did not match any of its variants')


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
    def __init__(self, sio, token, host_sid, player_infos, start_position):
        self.host_sid = host_sid
        self.token = token
        self.sio = sio
        # Create Evidence combination with new database connection
        DATABASES['game_init{}'.format(self.token)] = dj_database_url.config(conn_max_age=600)

        self.clues = self.generate_solution_clues()

        # TODO: Delete later. Frontend needs this for testing
        clues_dict = []
        for clue in self.clues:
            clues_dict.append(clue.__dict__)
        self.send_to_all(sio, 'solution_clues', {'clues': clues_dict})

        self.team_proofs = []
        self.mole_proofs = []
        self.players = []

        # Deep copy of the array so that the clue can be deleted when it is assigned to the players. This guarantees that each player is assigned a different proof
        clues_copy = []
        for clue in self.clues:
            clues_copy.append(deepcopy(clue))

        for player_id, player_info in enumerate(player_infos):
            clue = random.choice(clues_copy)
            self.players.append(Player(player_id, player_info['name'], player_info['sid'], self.get_clue_by_name(clue)))
            clues_copy.remove(clue)

        random.choice(self.players).is_mole = True

        self.turn_state: TurnState = TurnState()
        self.move_modifier: MoveModifier = MoveModifier.NORMAL

        self.map = small_map_shortcut()  # small test map
        start_position = DEFAULT_START_POSITION if start_position is None else start_position
        self.team_pos: pyllist.dllistnode = self.map.nodeat(start_position)
        self.moriarty_pos: pyllist.dllistnode = self.map.nodeat(0)
        self.debug_game_representation()  # test case debug

        # TODO: Serialize Map and send with init packet
        for player in self.players:
            clues = list(map(lambda c: c.__dict__, player.inventory))
            sio.emit(
                'init',
                {
                    'player_id': player.player_id,
                    'is_mole': player.is_mole,
                    'map': None,  # TODO: remove this
                    'clue': clues[0],  # TODO: remove this
                    'clues': clues
                },
                room=player.sid
            )

        self.send_players_turn(sio)

    def _get_player_info(self):
        return list(map(lambda p: {'player_id': p.player_id, 'name': p.name}, self.players))

    def player_disconnect(self, sio, sid):
        player = self.get_player(sid)
        if player is None:
            print('WARN: got disconnect from player, that could not be found.', file=sys.stderr)
            return
        player.connected = False
        sio.emit('player_disconnected', player.player_id, room=self.host_sid)
        print('player {} disconnected'.format(player.name))

    def player_rejoin(self, sio, sid, name):
        player = self.get_player_by_name(name)
        if player is None:
            print('WARN: got rejoin from player, that could not be found.', file=sys.stderr)
            return

        player.sid = sid
        player.connected = True

        sio.emit('player_rejoined', player.player_id, room=self.host_sid)
        clues = list(map(lambda c: c.__dict__, player.inventory))
        sio.emit(
            'init',
            {
                'player_id': player.player_id,
                'is_mole': player.is_mole,
                'map': None,  # TODO: remove this
                'clue': clues[0],  # TODO: remove this
                'clues': clues
            },
            room=player.sid
        )
        print('player {} rejoined'.format(player.name))

    def has_disconnected_player(self, name):
        for p in self.players:
            if p.name == name and not p.connected:
                return True
        return False

    def get_team_pos(self):
        """
        :rtype: Field
        :return: The Field the player is standing on
        """
        return self.team_pos.value

    def get_moriarty_pos(self):
        """
        :rtype: Field
        :return: The Field moriarty is standing on
        """
        return self.moriarty_pos.value

    def move_player(self, distance: int) -> int or None:
        """
        Moves the player over the map. Does not handle occasions.
        In case a minigame field is trespassed, the move is stopped and True is returned.

        :param distance: the number of fields to move
        :return: If a minigame field was reached, the number of remaining move distance is returned, otherwise None
        """
        for i in range(distance):
            self.team_pos = self.team_pos.next  # get next field
            if self.team_pos is None:
                self.game_over()  # raise NotImplementedError('End of map reached')
            else:
                field = self.get_team_pos()
                if field.type == FieldType.MINIGAME:
                    self.turn_state.player_turn_state = TurnState.PlayerTurnState.PLAYING_MINIGAME
                    remaining_distance = distance - i - 1
                    return remaining_distance
        return None

    def moriarty_move(self, sio):
        num_fields = random.randint(1, 2)
        for i in range(num_fields):
            if self.moriarty_pos.next is None:
                # Should not be possible
                # raise Exception('Moriarty reached end of map')  # TODO
                self.game_over() # Maybe allow the Team in the future to stall on the goal field to search for evidences
            self.moriarty_pos = self.moriarty_pos.next
            if self.get_moriarty_pos().index == self.get_team_pos().index:
                self.game_over("Mole Wins")
                # raise Exception('Moriarty caught players')  # TODO

        # TODO: remove follower_move, if frontend uses moriarty_move
        self.send_to_all(sio, 'follower_move', self.get_moriarty_pos().index)
        self.send_to_all(sio, 'moriarty_move', self.get_moriarty_pos().index)

    def send_players_turn(self, sio):
        self.send_to_all(
            sio,
            'players_turn',
            {'player_id': self.get_current_player().player_id, 'movement_modifier': self.move_modifier.name.lower()}
        )

    def end_player_turn(self, sio):
        """
        Moves the moriarty. Sets turn_state.player_id to a not disabled player.
        Removes disabling of all players, that are skipped, because of disable.
        """
        while True:
            self.moriarty_move(sio)
            self.turn_state.player_index = (self.turn_state.player_index + 1) % len(self.players)
            if self.get_current_player().disabled:
                self.get_current_player().disabled = False
                print('player "{}" is not longer disabled.'.format(self.get_current_player().name))
            else:
                self.send_players_turn(sio)
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
            if node == self.moriarty_pos:
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

    def get_player(self, sid) -> Player or None:
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
                'with': player_id,
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
            move_distance = int(move_distance * self.move_modifier.get_factor())
            self.move_modifier = MoveModifier.NORMAL
            # be merciful
            if move_distance == 0:
                move_distance = 1
            self.handle_movement(sio, move_distance)

        elif player_choice.get('type') == 'share-clue':
            player = self.get_player(sid)

            # Get player with whom the clue should be shared
            share_with = next((p for p in self.players if p.player_id == player_choice.get('with')), None)
            if share_with is None:
                raise InvalidUserException('Got invalid player id (with: {})'.format(player_choice.get('with')))

            # Get clue which should be shared
            clue = next((c for c in player.inventory if c.name == player_choice.get('clue')), None)
            if clue is None:
                raise InvalidUserException('Got invalid clue name (clue: {})'.format(player_choice.get('clue')))

            # Update sent_to value from players clue
            clue.sent_to.append(share_with.player_id)

            # Check if share_with player already has clue
            share_clue = self.check_and_add_clue(player.player_id, share_with, clue)

            # Share clue with share_with player
            share_clue = share_clue.__dict__
            sio.emit(
                'receive_clue',
                {'clue': share_clue},
                room=share_with.sid
            )
            # Send updated clue to player
            clue = clue.__dict__
            sio.emit(
                'updated_clue',
                {'clue': clue},
                room=player.sid
            )

            self.end_player_turn(sio)

        elif player_choice.get('type') == 'validate-clues':
            player = self.get_player(sid)
            clues = self.clues_dict_2_object(player_choice.get('clues'))

            # Validate only when all clues are available. Guessing is not allowed!
            successful_validation = self.validate_clues(clues) if self.validation_allowed(player.inventory, clues) else False

            # Always send back the clues that should be validated
            if successful_validation:
                self.add_verified_clues_to_proofs(clues, player.is_mole)
                self.send_to_all(self.sio, 'validation_result', {'successful_validation': successful_validation, 'clues': player_choice.get('clues')})
            else:
                sio.emit(
                    'validation_result',
                    {'successful_validation': successful_validation, 'clues': player_choice.get('clues')},
                    room=player.sid
                )

            self.end_player_turn(sio)

        elif player_choice.get('type') == 'search-clue':
            player = self.get_player(sid)
            clue = None

            if player_choice.get('success') is True:
                clue = self.get_random_missing_clue(player.inventory)
                self.add_clue(-1, player, clue)

                clue = clue.__dict__

            sio.emit(
                'receive_clue',
                {'clue': clue},
                room=player.sid
            )

            self.end_player_turn(sio)

    def handle_movement(self, sio, move_distance: int):
        """
        Moves the player while handling turn state, minigames and occasions.
        """

        remaining_moves = self.move_player(move_distance)
        self.send_to_all(sio, 'move', self.get_team_pos().index)

        # TODO remove second condition (self.get_team_pos().type == FieldType.SHORTCUT) to make shortcut fields possible
        if remaining_moves is not None: # or self.get_team_pos().type == FieldType.SHORTCUT:
            print("stepped on minigame, index:" + str(self.get_team_pos().index))
            if self.get_team_pos().type not in [FieldType.MINIGAME, FieldType.SHORTCUT]:
                raise AssertionError(
                    'got remaining moves, but not on minigame field.\ncurrent field type: {}'.format(
                        self.get_team_pos().type.name
                    )
                )
            self.turn_state.start_minigame(remaining_moves)
            self.trigger_minigame()
            self.send_to_all(sio, 'minigame', 'not implemented')

            self.end_player_turn(sio)  # TODO: remove this, if minigames are implemented
        elif self.get_team_pos().type == FieldType.OCCASION:  # check occasion field
            print("stepped on occasion, index:" + str(self.get_team_pos().index))
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
            # todo
            # if minigame was won
            jump = self.get_team_pos().shortcut_field - self.get_team_pos().index
            print("stepped on shortcut field, jump:" + str(jump) + " index:" + str(self.get_team_pos().index))
            self.move_player(jump)
            # if minigame was lost
            # do nothing stay at spot or walk remaining moves
            self.end_player_turn(sio)
        elif self.get_team_pos().type == FieldType.Goal:
            print("stepped on goal field, index:" + str(self.get_team_pos().index))
            self.game_over()
        else:
            print("stepped on normal field, index:" + str(self.get_team_pos().index))
            self.end_player_turn(sio)

    def player_occasion_choice(self, sio, sid, chosen_occasion: dict):
        """
        This event is called, if a player chose an occasion.

        - found clue:
            chosen_occasion is in the following form:
            {
                'type': 'found_clue',
                'success': true/false,
            }

        - move forwards:
            chosen_occasion is in the following form:
            {
                'type': 'move_forwards',
                'value': 6,
            }

        - simplify dicing:
            chosen_occasion is in the following form:
            {
                'type': 'simplify_dicing',
            }

        - skip player:
            chosen_occasion is in the following form:
            {
                'type': 'skip_player',
                'player_id': player_id,
            }

        - hinder dicing:
            chosen_occasion is in the following form:
            {
                'type': 'hinder_dicing',
            }
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

        self.turn_state.occasion_choices = None  # reset occasion choices

        sio.emit('occasion_info', chosen_occasion, room=self.host_sid)

        if occasion_type == 'found_clue':
            player = self.get_player(sid)
            clue = None

            if chosen_occasion.get('success') is True:
                clue = self.get_random_missing_clue(player.inventory)
                self.add_clue(-1, player, clue)

                clue = clue.__dict__

            sio.emit(
                'receive_clue',
                {'clue': clue},
                room=player.sid
            )

            self.end_player_turn(sio)

        elif occasion_type == 'move_forwards':
            num_fields = chosen_occasion.get('value')
            if num_fields is None:
                raise InvalidMessageException(
                    'Invalid occasion choice message from client. Missing "value" in move_forwards.'
                )

            num_fields = int(num_fields)
            self.handle_movement(sio, num_fields)

        elif occasion_type == 'simplify_dicing':
            self.move_modifier = MoveModifier.SIMPLIFY
            self.end_player_turn(sio)

        elif occasion_type == 'skip_player':
            skip_player = next((p for p in self.players if p.player_id == chosen_occasion.get('player_id')), None)
            if skip_player is None:
                raise InvalidMessageException(
                    'Could not find player with id "{}"'.format(chosen_occasion.get('player_id'))
                )

            skip_player.disabled = True
            self.end_player_turn(sio)

        elif occasion_type == 'hinder_dicing':
            self.move_modifier = MoveModifier.HINDER
            self.end_player_turn(sio)
        else:
            raise InvalidMessageException('type of occasion choice is invalid: "{}"'.format(occasion_type))

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

    # todo move to player
    def add_clue(self, received_from, player, clue):
        # Reset received_from and sent_to information
        clue_copy = Clue(name=clue.name, type=clue.type, subtype=clue.subtype, received_from=received_from)

        player.inventory.append(clue_copy)
        return clue_copy

    def check_and_add_clue(self, received_from, player, clue):
        for c in player.inventory:
            if c.name == clue.name:
                return c

        return self.add_clue(received_from, player, clue)

    def get_random_missing_clue(self, clues):
        """
        :rtype: Evidence
        :return: Get a random clue, which the player does not have yet
        """
        missing_clues = []

        for clue in self.clues:
            c = next((c for c in clues if c.name == clue.name), None)

            if c is None:
                missing_clues.append(clue)

        return random.choice(missing_clues)

    def get_clue_by_name(self, clue):
        for c in self.clues:
            if c.name == clue.name:
                return c

    # todo move to fassade static
    def evidence_2_clue(self, evidence):
        return Clue(name=evidence.name, type=evidence.type, subtype=evidence.subtype)

    # todo move to fassade static
    def clues_dict_2_object(self, clues):
        """
        :rtype: list[Evidence]
        :return: Converted clues
        """
        converted_clues = []

        for clue in clues:
            converted_clues.append(Evidence(name=clue['name'], type=clue['type'], subtype=clue['subtype']))

        return converted_clues

    def validation_allowed(self, player_clues, clues):
        clue_type = clues[0].type

        for clue in clues:
            # The clue type must be the same for all clues
            if clue.type != clue_type:
                return False

            # The clues must be in the players inventory
            result = next((c for c in player_clues if c.name == clue.name), None)

            if result is None:
                return False

        return True

    def validate_clues(self, clues):
        """
        :rtype: Bool
        :return: Bool whether the correct clues were found or not
        """
        clue_type = clues[0].type
        clue_group = []

        # Get all winner clues with requested clue type
        for clue in self.clues:
            if clue.type == clue_type:
                clue_group.append(clue)

        # Check if player has all the clues needed
        for clue in clues:
            if clue.type != clue_type:
                return False

            result = next((e for e in clue_group if e.name == clue.name), None)
            if result is not None:
                clue_group.remove(result)

        return len(clue_group) == 0

    def add_verified_clues_to_proofs(self, clues, is_mole):
        # Check if the verified clues have already been added to the other teams proofs or self proofs
        for clue in clues:
            if is_mole is True and next((c for c in self.team_proofs if c.name == clue.name), None) is None and next((c for c in self.mole_proofs if c.name == clue.name), None) is None:
                self.mole_proofs.append(clue)
            elif is_mole is False and next((c for c in self.mole_proofs if c.name == clue.name), None) is None and next((c for c in self.team_proofs if c.name == clue.name), None) is None:
                self.team_proofs.append(clue)

    def generate_solution_clues(self):
        """
        :rtype: list[Evidence]
        :return: List of clues to win the game
        """
        clues = []
        db_connection = 'game_init{}'.format(self.token)

        all_weapon_objects = Evidence.objects.using(db_connection).filter(type=ClueType.WEAPON,
                                                                          subtype=ClueSubtype.OBJECT)
        all_weapon_colors = Evidence.objects.using(db_connection).filter(type=ClueType.WEAPON,
                                                                         subtype=ClueSubtype.COLOR)
        all_weapon_conditions = Evidence.objects.using(db_connection).filter(type=ClueType.WEAPON,
                                                                             subtype=ClueSubtype.CONDITION)
        clues.append(self.evidence_2_clue(random.choice(all_weapon_objects)))
        clues.append(self.evidence_2_clue(random.choice(all_weapon_colors)))
        clues.append(self.evidence_2_clue(random.choice(all_weapon_conditions)))

        all_crime_scene_locations = Evidence.objects.using(db_connection).filter(type=ClueType.CRIME_SCENE,
                                                                                 subtype=ClueSubtype.LOCATION)
        all_crime_scene_temperature = Evidence.objects.using(db_connection).filter(type=ClueType.CRIME_SCENE,
                                                                                   subtype=ClueSubtype.TEMPERATURE)
        all_crime_scene_districts = Evidence.objects.using(db_connection).filter(type=ClueType.CRIME_SCENE,
                                                                                 subtype=ClueSubtype.DISTRICT)
        clues.append(self.evidence_2_clue(random.choice(all_crime_scene_locations)))
        clues.append(self.evidence_2_clue(random.choice(all_crime_scene_temperature)))
        clues.append(self.evidence_2_clue(random.choice(all_crime_scene_districts)))

        all_offender_escape_clothings = Evidence.objects.using(db_connection).filter(type=ClueType.OFFENDER,
                                                                                     subtype=ClueSubtype.CLOTHING)
        all_offender_escape_sizes = Evidence.objects.using(db_connection).filter(type=ClueType.OFFENDER,
                                                                                 subtype=ClueSubtype.SIZE)
        all_offender_escape_characteristics = Evidence.objects.using(db_connection).filter(type=ClueType.OFFENDER,
                                                                                           subtype=ClueSubtype.CHARACTERISTIC)
        clues.append(self.evidence_2_clue(random.choice(all_offender_escape_clothings)))
        clues.append(self.evidence_2_clue(random.choice(all_offender_escape_sizes)))
        clues.append(self.evidence_2_clue(random.choice(all_offender_escape_characteristics)))

        all_time_of_crime_weekdays = Evidence.objects.using(db_connection).filter(type=ClueType.TIME_OF_CRIME,
                                                                                  subtype=ClueSubtype.WEEKDAY)
        all_time_of_crime_daytimes = Evidence.objects.using(db_connection).filter(type=ClueType.TIME_OF_CRIME,
                                                                                  subtype=ClueSubtype.DAYTIME)
        all_time_of_crime_times = Evidence.objects.using(db_connection).filter(type=ClueType.TIME_OF_CRIME,
                                                                               subtype=ClueSubtype.TIME)
        clues.append(self.evidence_2_clue(random.choice(all_time_of_crime_weekdays)))
        clues.append(self.evidence_2_clue(random.choice(all_time_of_crime_daytimes)))
        clues.append(self.evidence_2_clue(random.choice(all_time_of_crime_times)))

        all_mean_of_escape_conditions = Evidence.objects.using(db_connection).filter(type=ClueType.MEANS_OF_ESCAPE,
                                                                                     subtype=ClueSubtype.MODEL)
        all_mean_of_escape_daytime = Evidence.objects.using(db_connection).filter(type=ClueType.MEANS_OF_ESCAPE,
                                                                                  subtype=ClueSubtype.COLOR)
        all_mean_of_escape_districts = Evidence.objects.using(db_connection).filter(type=ClueType.MEANS_OF_ESCAPE,
                                                                                    subtype=ClueSubtype.ESCAPE_ROUTE)
        clues.append(self.evidence_2_clue(random.choice(all_mean_of_escape_conditions)))
        clues.append(self.evidence_2_clue(random.choice(all_mean_of_escape_daytime)))
        clues.append(self.evidence_2_clue(random.choice(all_mean_of_escape_districts)))

        return clues

    def game_over(self, result=None):
        self.turn_state.game_over()
        # if mole player won
        # let everybody guess one last time?
        # check if any players clues match the goal clues
        if result is None:
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
        self.shortcut_field = shortcut_field    # int
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
    map_dll.append(Field(FieldType.WALKABLE))  # was Minigame
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.OCCASION))
    map_dll.append(Field(FieldType.OCCASION))
    map_dll.append(Field(FieldType.SHORTCUT, 18))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.WALKABLE))  # was Minigame
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
    map_dll.append(Field(FieldType.WALKABLE))  # was Minigame
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.OCCASION))
    map_dll.append(Field(FieldType.OCCASION))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.SHORTCUT, 18))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.OCCASION))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.WALKABLE))  # was Minigame
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
