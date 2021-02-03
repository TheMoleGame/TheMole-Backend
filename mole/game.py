# -*- coding: utf-8 -*-
import sys
import time
from copy import deepcopy
from enum import Enum
import random
import pyllist
import dj_database_url
from django.db import connections

from .models import Evidence, ClueType, ClueSubtype
from .game_character import *
from mole_backend.settings import DATABASES
from .pantomime import PANTOMIME_WORDS, PantomimeState

OCCASIONS = ['found_clue', 'move_forwards', 'simplify_dicing', 'skip_player', 'hinder_dicing']
DEFAULT_START_POSITION = 4

random.seed(time.time())


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

    def __repr__(self):
        parts = ['(player_index: {}  state: {}'.format(self.player_index, self.player_turn_state.name)]
        if self.occasion_choices is not None:
            parts.append(str(self.occasion_choices))
        if self.remaining_move_distance:
            parts.append(str(self.remaining_move_distance))
        return '  '.join(parts) + ')'


def _random_occasion_choices(test_choices=None):
    choices = []

    if test_choices is not None and len(test_choices) >= 1 and test_choices[0] is not None:
        # Add first test choice
        choices.append(test_choices[0])

        if len(test_choices) == 1:
            # Add random choice
            choices_copy = OCCASIONS.copy()
            choices_copy.remove(test_choices[0])
            choices.append(random.choice(choices_copy))

        elif len(test_choices) == 2 and test_choices[1] is not None:
            # Add second test choice
            choices.append(test_choices[1])
    else:
        # Add random choices
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
    def __init__(
            self, sio, token, host_sid, player_infos, start_position, test_choices=None, all_proofs=False,
            enable_minigames=False
    ):
        self.host_sid = host_sid
        self.token = token
        self.sio = sio
        self.test_choices = test_choices
        self.enable_minigames = enable_minigames

        # Create Evidence combination
        self.clues = self.generate_solution_clues()

        # TODO: Delete later. Frontend needs this for testing
        clues_dict = []
        for clue in self.clues:
            clues_dict.append(clue.__dict__)
        self.send_to_all(sio, 'solution_clues', {'clues': clues_dict})

        self.team_proofs = []
        self.mole_proofs = []
        self.players = []

        # Deep copy of the array so that the clue can be deleted when it is assigned to the players.
        # This guarantees that each player is assigned a different proof
        clues_copy = []
        for clue in self.clues:
            clues_copy.append(deepcopy(clue))

        for player_id, player_info in enumerate(player_infos):
            if all_proofs is None or all_proofs is False:
                # Assign random clue
                clue = random.choice(clues_copy)
                self.players.append(
                    Player(player_id, player_info['name'], player_info['sid'], self.get_clue_by_name(clue))
                )
                clues_copy.remove(clue)
            else:
                # Assign all clues
                player = Player(player_id, player_info['name'], player_info['sid'])
                player.inventory = self.clues
                self.players.append(player)

        random.choice(self.players).is_mole = True

        self.turn_state: TurnState = TurnState()
        self.move_modifier: MoveModifier = MoveModifier.NORMAL
        self.pantomime_state: PantomimeState or None = None

        self.pantomime_category_count = {}
        for difficulty, category_list in PANTOMIME_WORDS.items():
            self.pantomime_category_count[difficulty] = {}
            for category in category_list:
                self.pantomime_category_count[difficulty][category] = 0

        self.map = create_map()
        got_start_position = True if start_position is not None else False
        start_position = DEFAULT_START_POSITION if start_position is None else start_position
        self.team_pos: pyllist.dllistnode = self.map.nodeat(start_position)
        self.moriarty_pos: pyllist.dllistnode = self.map.nodeat(0)
        self.debug_game_representation()  # test case debug

        for player in self.players:
            clues = list(map(lambda c: c.__dict__, player.inventory))
            sio.emit(
                'init',
                {
                    'player_id': player.player_id,
                    'is_mole': player.is_mole,
                    'clues': clues,
                    'rejoin': False,
                },
                room=player.sid
            )

        if got_start_position:
            self.send_to_all(sio, 'move', self.get_team_pos().index)

        self.send_players_turn(sio)

    def tick(self, sio):
        # check minigame time over
        if self.turn_state.player_turn_state == TurnState.PlayerTurnState.PLAYING_MINIGAME:
            if self.pantomime_state.is_timeout():
                self.evaluate_pantomime(sio)

    def _get_player_info(self):
        return list(map(lambda p: {'player_id': p.player_id, 'name': p.name}, self.players))

    def has_connected_player(self):
        return any(map(lambda player: player.connected, self.players))

    def player_disconnect(self, sio, sid):
        player = self.get_player(sid)
        if player is None:
            print('WARN: got disconnect from player, that could not be found.', file=sys.stderr)
            return

        # handle if current player disconnects
        if self.get_current_player().sid == sid:
            self.end_player_turn(sio, do_moriarty_move=False)
            self.turn_state.occasion_choices = None
            self.turn_state.remaining_move_distance = 0

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
        player_info = list(map(lambda p: {'name': p.name, 'player_id': p.player_id}, self.players))
        sio.emit('player_infos', player_info, room=player.sid)
        clues = list(map(lambda c: c.__dict__, player.inventory))
        sio.emit(
            'init',
            {
                'player_id': player.player_id,
                'is_mole': player.is_mole,
                'map': None,  # TODO: remove this
                'clue': clues[0],  # TODO: remove this
                'clues': clues,
                'rejoin': True,
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
                self.game_over(GameOverReason.REACHED_END_OF_MAP)
            else:
                field = self.get_team_pos()
                if field.type == FieldType.SHORTCUT and self.enable_minigames:
                    self.turn_state.player_turn_state = TurnState.PlayerTurnState.PLAYING_MINIGAME
                    remaining_distance = distance - i - 1
                    return remaining_distance
        return None

    def moriarty_move(self, sio):
        num_fields = random.choice([1, 1, 1, 2])
        for i in range(num_fields):
            if self.moriarty_pos.next is None:
                # TODO: Maybe allow the Team in the future to stall on the goal field to search for evidences
                self.game_over(GameOverReason.MORIARTY_CAUGHT)
            self.moriarty_pos = self.moriarty_pos.next
            if self.get_moriarty_pos().index == self.get_team_pos().index:
                self.game_over(GameOverReason.MORIARTY_CAUGHT)

        self.send_to_all(sio, 'moriarty_move', self.get_moriarty_pos().index)

    def send_players_turn(self, sio):
        self.send_to_all(
            sio,
            'players_turn',
            {'player_id': self.get_current_player().player_id, 'movement_modifier': self.move_modifier.name.lower()}
        )

    def end_player_turn(self, sio, do_moriarty_move=True):
        """
        Moves the moriarty. Sets turn_state.player_id to a not disabled player.
        Removes disabling of all players, that are skipped, because of disable.
        """
        while self.has_connected_player():
            if do_moriarty_move:
                self.moriarty_move(sio)
            do_moriarty_move = True

            self.turn_state.player_index = (self.turn_state.player_index + 1) % len(self.players)
            if self.get_current_player().disabled:
                self.get_current_player().disabled = False
                print('player "{}" is not longer disabled.'.format(self.get_current_player().name))
                sio.emit(
                    'occasion_info',
                    {'type': 'unskip_player', 'player_id': self.get_current_player().player_id},
                    room=self.host_sid
                )
            elif not self.get_current_player().connected:
                print('skipping player "{}" as he is disconnected'.format(self.get_current_player().name))
                do_moriarty_move = False  # If we skipped a disconnected player, moriarty also does not move
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
        player = self.get_player(sid)
        player_name = '<unknown>' if player is None else player.name

        if not self.players_turn(sid):
            raise InvalidMessageException(
                'Got player_choice, but it\'s not his turn.\n\tplayer_name: {}\n\tgame_token: {}'
                .format(player_name, self.token)
            )

        if self.turn_state.player_turn_state != TurnState.PlayerTurnState.PLAYER_CHOOSING:
            raise InvalidMessageException(
                'Got player_choice, but it\'s not the right moment for this message.'
                '\n\tplayer_name: {}\n\tturn_state: {}\n\tgame_token: {}'
                .format(player_name, repr(self.turn_state), self.token)
            )

        if player_choice.get('type') == 'dice':
            move_distance = int(player_choice.get('value'))
            if self.move_modifier == MoveModifier.HINDER:
                sio.emit(
                    'occasion_info',
                    {'type': 'unhinder_dicing', 'player_id': self.get_current_player().player_id},
                    room=self.host_sid
                )
            elif self.move_modifier == MoveModifier.SIMPLIFY:
                sio.emit(
                    'occasion_info',
                    {'type': 'unsimplify_dicing', 'player_id': self.get_current_player().player_id},
                    room=self.host_sid
                )
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
                raise InvalidMessageException(
                    'Got player_choice (share-clue), but share_with player_id is invalid:\n\twith: {}'
                    .format(player_choice.get('with'))
                )

            # Get clue which should be shared
            clue = next((c for c in player.inventory if c.name == player_choice.get('clue')), None)
            if clue is None:
                raise InvalidMessageException(
                    'Got player_choice (share-clue), with invalid clue name (clue: {})'
                    .format(player_choice.get('clue'))
                )

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

            sio.emit(
                'secret_move',
                {'player_id': player.player_id, 'move_name': 'share-clue'},
                room=self.host_sid
            )

            self.end_player_turn(sio)

        elif player_choice.get('type') == 'validate-clues':
            player = self.get_player(sid)
            clues = self.clues_dict_2_object(player_choice.get('clues'))

            # Validate only when all clues are available. Guessing is not allowed!
            validation_allowed, validation_status = self.validation_allowed(player.inventory, clues, player.is_mole)
            successful_validation = self.validate_clues(clues) if validation_allowed else False

            # Always send back the clues that should be validated
            if successful_validation:
                validation_status = 'new_validation'
                self.add_verified_clues_to_proofs(clues, player.is_mole)

            self.send_to_all(
                self.sio,
                'validation_result',
                {
                    'successful_validation': successful_validation,
                    'validation_status': validation_status,
                    'player_id': player.player_id,
                    'clues': player_choice.get('clues')
                }
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

            sio.emit(
                'secret_move',
                {'player_id': player.player_id, 'move_name': 'search-clue'},
                room=self.host_sid
            )

            self.end_player_turn(sio)

    def handle_movement(self, sio, move_distance: int):
        """
        Moves the player while handling turn state, minigames and occasions.
        """

        remaining_moves = self.move_player(move_distance)
        self.send_to_all(sio, 'move', self.get_team_pos().index)

        if self.get_team_pos().type is FieldType.SHORTCUT:
            print("stepped on shortcut, index:" + str(self.get_team_pos().index))
            if remaining_moves is None and self.enable_minigames:
                raise AssertionError('got no remaining moves on shortcut field.')
            if self.enable_minigames:
                self.turn_state.start_minigame(remaining_moves)
                self.trigger_pantomime(sio, self.get_team_pos().difficulty)
            else:
                self.turn_state.player_turn_state = TurnState.PlayerTurnState.PLAYER_CHOOSING
                team_pos = self.get_team_pos()
                move_distance = team_pos.shortcut_field - team_pos.index
                self.turn_state.remaining_move_distance = 0
                self.handle_movement(sio, move_distance)
        elif self.get_team_pos().type == FieldType.OCCASION:  # check occasion field
            print("stepped on occasion, index:" + str(self.get_team_pos().index))
            occasion_choices = _random_occasion_choices(self.test_choices)
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
        elif self.get_team_pos().type == FieldType.Goal:
            print("stepped on goal field, index:" + str(self.get_team_pos().index))
            self.game_over(GameOverReason.REACHED_END_OF_MAP)
        elif self.get_team_pos().type == FieldType.WALKABLE:
            print("stepped on normal field, index:" + str(self.get_team_pos().index))
            self.end_player_turn(sio)
        else:
            raise AssertionError('Unknown Field Type: {}'.format(self.get_team_pos().type))

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
        print('got player occasion choice: {}'.format(chosen_occasion))
        player = self.get_player(sid)
        player_name = '<unknown>' if player is None else player.name

        if not self.players_turn(sid):
            raise InvalidMessageException(
                'Got player_choice, but it\'s not his turn.\n\tplayer_name: {}\n\tgame_token: {}'
                .format(player_name, self.token)
            )

        # check whether player was in turn to choose occasion
        if self.turn_state.player_turn_state != TurnState.PlayerTurnState.PLAYER_CHOOSING_OCCASION:
            raise InvalidMessageException(
                'Got player_choice, but it\'s not the right moment for this message.'
                '\n\tplayer_name: {}\n\tturn_state: {}\n\tgame_token: {}'
                .format(player_name, repr(self.turn_state), self.token)
            )

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

    def _get_pantomime_category(self, difficulty):
        usages = self.pantomime_category_count[difficulty]
        usages = sorted(usages.items(), key=lambda u: u[1])
        lowest_usage = usages[0][1]
        usages = filter(lambda u: u[1] == lowest_usage, usages)
        category = random.choice(list(usages))[0]
        return category

    def trigger_pantomime(self, sio, difficulty):
        category = self._get_pantomime_category(difficulty)
        words = PANTOMIME_WORDS[difficulty][category]
        self.pantomime_category_count[difficulty][category] += 1

        solution_word = random.choice(words)
        self.pantomime_state = PantomimeState(solution_word, words, category)

        # inform host
        sio.emit('guess_pantomime', {'words': words, 'category': category, 'start': False}, room=self.host_sid)
        for player in self.players:
            if player.sid == self.get_current_player().sid:
                sio.emit(
                    'host_pantomime',
                    {'solution_word': solution_word, 'words': words, 'category': category},
                    room=player.sid
                )
            else:
                sio.emit('guess_pantomime', {'words': words, 'category': category, 'start': False}, room=player.sid)

    def pantomime_start(self, sio, sid):
        # check if in pantomime
        if not self.turn_state.player_turn_state == TurnState.PlayerTurnState.PLAYING_MINIGAME:
            raise InvalidMessageException('Got pantomime start, but not in minigame\n\tsid: {}'.format(sid))
        if self.pantomime_state is None:
            raise AssertionError('pantomime_state is None in minigame')

        # get player
        player = self.get_player(sid)
        if player is None:
            raise InvalidMessageException('Could not find player with sid: {}'.format(sid))
        if player.sid != self.get_current_player().sid:
            raise InvalidMessageException('Got pantomime start from player that is not hosting.')
        self.pantomime_state.start_timeout()

        for player in self.players:
            if player.sid != self.get_current_player().sid:
                sio.emit(
                    'guess_pantomime',
                    {
                        'words': self.pantomime_state.words,
                        'category': self.pantomime_state.category,
                        'start': True
                    },
                    room=player.sid
                )

    def pantomime_choice(self, sio, sid, message):
        # check if in pantomime
        if not self.turn_state.player_turn_state == TurnState.PlayerTurnState.PLAYING_MINIGAME:
            raise InvalidMessageException('Got pantomime choice, but not in minigame\n\tsid: {}'.format(sid))
        if self.pantomime_state is None:
            raise AssertionError('pantomime_state is None in minigame')
        if not self.pantomime_state.timeout_started():
            raise InvalidMessageException('game has not started, but got pantomime choice')

        # get player
        player = self.get_player(sid)
        if player is None:
            raise InvalidMessageException('Could not find player with sid: {}'.format(sid))
        if player.sid == self.get_current_player().sid:
            raise InvalidMessageException('Got pantomime choice from hosting player.')

        # validate message
        if not isinstance(message, dict):
            raise InvalidMessageException('Got pantomime choice, but message is no dictionary')
        guess = message.get('guess')
        if guess is None:
            raise InvalidMessageException(
                'Got Pantomime choice without key "guess". Message keys: {}'.format(message.keys())
            )
        if guess not in self.pantomime_state.words:
            raise InvalidMessageException(
                'Got invalid guess "{}". Not in possible words: {}'.format(guess, self.pantomime_state.words)
            )

        self.pantomime_state.guesses[player.player_id] = guess

        # evaluate, if everyone has answered
        if len(self.pantomime_state.guesses) == len(self.players)-1:
            self.evaluate_pantomime(sio)

    def evaluate_pantomime(self, sio):
        player_results = []
        overall_success = True
        for player in self.players:
            # skip disconnected players and host player
            if not player.connected or player.sid == self.get_current_player().sid:
                continue
            player_guess = self.pantomime_state.guesses.get(player.player_id)
            success = player_guess == self.pantomime_state.solution_word
            if not success:
                overall_success = False
            player_results.append({
                'player_id': player.player_id,
                'success': success,
                'guess': player_guess,
            })

        message = {
            'success': overall_success,
            'player_results': player_results,
            'solution_word': self.pantomime_state.solution_word
        }

        self.send_to_all(sio, 'pantomime_result', message)

        self.pantomime_state = None
        if overall_success:
            # go shortcut
            self.turn_state.player_turn_state = TurnState.PlayerTurnState.PLAYER_CHOOSING  # this is kinda hacky
            team_pos = self.get_team_pos()
            move_distance = team_pos.shortcut_field - team_pos.index + self.turn_state.remaining_move_distance
            self.turn_state.remaining_move_distance = 0
            self.handle_movement(sio, move_distance)
        else:
            self.turn_state.remaining_move_distance = 0
            self.end_player_turn(sio)

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

    def validation_allowed(self, player_clues, clues, is_mole):
        clue_type = clues[0].type

        for clue in clues:
            # The clue type must be the same for all clues
            if clue.type != clue_type:
                return False, 'different_clue_types'

            # The clues must be in the players inventory
            result = next((c for c in player_clues if c.name == clue.name), None)

            if result is None:
                return False, 'not_in_inventory'

        # Check if the clues have already been verified
        if self.is_not_verified(clues, is_mole):
            return True, 'validation_allowed'
        else:
            return False, 'already_verified'

    def is_not_verified(self, clues, is_mole):
        # Check if the verified clues have already been added to the other teams proofs or self proofs
        for clue in clues:
            if is_mole is True and next((c for c in self.team_proofs if c.name == clue.name), None) is None and next((c for c in self.mole_proofs if c.name == clue.name), None) is None:
                return True
            elif is_mole is False and next((c for c in self.mole_proofs if c.name == clue.name), None) is None and next((c for c in self.team_proofs if c.name == clue.name), None) is None:
                return True

        return False

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
        for clue in clues:
            if is_mole is True:
                self.mole_proofs.append(clue)
            elif is_mole is False:
                self.team_proofs.append(clue)

    def generate_solution_clues(self):
        """
        :rtype: list[Evidence]
        :return: List of clues to win the game
        """

        # Use new database connection
        db_connection = 'game_init{}'.format(self.token)
        DATABASES[db_connection] = dj_database_url.config(conn_max_age=600)

        clues = []

        all_weapon_objects = Evidence.objects.using(db_connection).filter(type=ClueType.WEAPON,
                                                                          subtype=ClueSubtype.OBJECT)
        all_weapon_colors = Evidence.objects.using(db_connection).filter(type=ClueType.WEAPON,
                                                                         subtype=ClueSubtype.COLOR_W)
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
                                                                                  subtype=ClueSubtype.COLOR_ME)
        all_mean_of_escape_districts = Evidence.objects.using(db_connection).filter(type=ClueType.MEANS_OF_ESCAPE,
                                                                                    subtype=ClueSubtype.ESCAPE_ROUTE)
        clues.append(self.evidence_2_clue(random.choice(all_mean_of_escape_conditions)))
        clues.append(self.evidence_2_clue(random.choice(all_mean_of_escape_daytime)))
        clues.append(self.evidence_2_clue(random.choice(all_mean_of_escape_districts)))

        connections[db_connection].close()

        return clues

    def game_over(self, reason=GameOverReason.DEFAULT):
        self.turn_state.game_over()
        winner = "mole"
        # Team reached end without evidences and mole has no evidences, presumption of innocence
        message = "hindered_team"

        if reason is GameOverReason.MORIARTY_CAUGHT:
            message = "moriarty_caught_team"
        elif reason is GameOverReason.DEFAULT or GameOverReason.REACHED_END_OF_MAP:
            # Reminder: We have 5 categories of proofs
            # improvement thoughts:
            # Harder but more logical would be to compare the proofs he found with the teams proofs
            # then subtract the moles proofs from the teams

            # Mole wins if he has verified at least two proofs (Reminder: 3 clues per proof)
            if len(self.mole_proofs) >= (2 * 3):
                message = "destroyed_enough_proofs"
            # Team wins if it has verified at least four proofs (Reminder: 3 clues per proof)
            elif len(self.team_proofs) >= (4 * 3):
                # story could be such that the remaining proofs can be found by an investigator at the court
                winner = "team"
                message = "validated_enough_proofs"

        print('---------------------------------------------\n' +
              '--------------GAME OVER----------------------\n' +
              '---------------------------------------------\n' +
              '----------------' + str(reason.name) + '------------------------')

        mole_id = None
        for player in self.players:
            if player.is_mole:
                mole_id = player.player_id
        self.send_to_all(self.sio, 'gameover', {'winner': winner, 'reason': message, 'mole_id': mole_id})


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
    DEVIL_FIELD = 'devil_field'
    SHORTCUT = 'shortcut'
    Goal = 'goal'


class Field(dict):
    counter = 0

    def __init__(self, field_type=FieldType.WALKABLE, shortcut_field=None, difficulty=None):
        if field_type == FieldType.SHORTCUT and difficulty is None:
            raise AssertionError('cant create SHORTCUT without difficulty level')
        dict.__init__(self, index=Field.counter)
        self.index = Field.counter
        Field.counter = Field.counter + 1
        self.shortcut_field = shortcut_field    # int
        self.difficulty = difficulty
        self.type = field_type                  # type: FieldType
        dict.__setitem__(self, "shortcut", self.shortcut_field)
        dict.__setitem__(self, "field_type", self.type)


class InvalidMessageException(Exception):
    pass


def create_map():
    # reset counter
    Field.counter = 0

    map_dll = pyllist.dllist()  # double linked List

    for i in range(4):
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
    map_dll.append(Field(FieldType.SHORTCUT, 18, 'easy'))  # id == 14
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.OCCASION))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.WALKABLE))
    # Second Section
    map_dll.append(Field(FieldType.WALKABLE))  # id == 23
    map_dll.append(Field(FieldType.OCCASION))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.SHORTCUT, 33, 'medium'))

    map_dll.append(Field(FieldType.OCCASION))
    map_dll.append(Field(FieldType.OCCASION))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.OCCASION))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.OCCASION))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.SHORTCUT, 42, 'hard'))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.OCCASION))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.Goal))
    return map_dll
