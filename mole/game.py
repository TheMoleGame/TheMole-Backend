# -*- coding: utf-8 -*-
import enum
import itertools
import sys
import time
from copy import deepcopy
import random
import dj_database_url
import requests
from django.db import connections

from .occasions import _random_occasion_choices
from .turn_state import TurnState, GameOverReason, MoveModifier
from .map import Field, FieldType, create_map, pyllist
from .clues import Clue, clues_dict_2_object, evidence_2_clue, Proof
from .models import Evidence, ClueType, ClueSubtype
from .game_character import *
from mole_backend.settings import DATABASES
from .pantomime import PANTOMIME_WORDS, PantomimeState
from .drawgame import DRAWGAME_WORDS, DrawgameState

DEFAULT_START_POSITION = 4
MORIARTY_AUTO_MOVE_INTERVAL = (30, 40)
MORIARTY_HIDE_DURATION = 60*3

random.seed(time.time())


class DifficultyLevel(enum.Enum):
    EASY = 0
    MEDIUM = 1
    HARD = 2


def _parse_difficulty(difficulty):
    for level in DifficultyLevel:
        if level.name.lower() == difficulty.lower():
            return level
    raise ValueError('Unknown difficulty level: {}'.format(difficulty))


class Game:
    def __init__(
            self, sio, token, desktop_sid, player_infos, start_position, test_choices=None, all_proofs=False,
            enable_minigames=False, moriarty_position=0, difficulty='easy'
    ):
        self.desktop_sid = desktop_sid
        self.token = token
        self.sio = sio
        self.test_choices = test_choices
        self.enable_minigames = enable_minigames
        self.difficulty = _parse_difficulty(difficulty)

        # Create Evidence combination
        self.solution_clues = self.generate_solution_clues()

        # TODO: Delete later. Frontend needs this for testing
        clues_dict = []
        for clue in self.solution_clues:
            clues_dict.append(clue.to_dict())
        self.send_to_all(sio, 'solution_clues', {'clues': clues_dict})

        self.team_proofs = []  # type: List[Proof]
        self.mole_proofs = []  # type: List[Proof]
        self.players = []

        # Deep copy of the array so that the clue can be deleted when it is assigned to the players.
        # This guarantees that each player is assigned a different proof
        solution_clues_copy = deepcopy(self.solution_clues)

        for player_id, player_info in enumerate(player_infos):
            if all_proofs is None or all_proofs is False:
                # Assign random clue
                clue = random.choice(solution_clues_copy)
                self.players.append(
                    Player(player_id, player_info['name'], player_info['sid'], self.get_clue_by_name(clue.name))
                )
                solution_clues_copy.remove(clue)
            else:
                # Assign all clues
                player = Player(player_id, player_info['name'], player_info['sid'])
                player.inventory = deepcopy(self.solution_clues)
                self.players.append(player)

        random.choice(self.players).is_mole = True

        self.turn_state: TurnState = TurnState()
        self.move_modifier: MoveModifier = MoveModifier.NORMAL
        self.pantomime_state: PantomimeState or None = None
        self.drawgame_state: DrawgameState or None = None

        self.moriarty_hide_time = None

        self.pantomime_category_count = {}
        for difficulty, category_list in PANTOMIME_WORDS.items():
            self.pantomime_category_count[difficulty] = {}
            for category in category_list:
                self.pantomime_category_count[difficulty][category] = 0

        self.drawgame_category_count = {}
        for difficulty, category_list in DRAWGAME_WORDS.items():
            self.drawgame_category_count[difficulty] = {}
            for category in category_list:
                self.drawgame_category_count[difficulty][category] = 0

        self.map = create_map()
        got_start_position = True if start_position is not None else False
        start_position = DEFAULT_START_POSITION if start_position is None else start_position
        self.team_pos: pyllist.dllistnode = self.map.nodeat(start_position)
        self.moriarty_pos: pyllist.dllistnode = self.map.nodeat(moriarty_position)
        moriarty_move_interval = self._get_moriarty_move_interval()
        if moriarty_move_interval is not None:
            self.next_moriarty_move_time = time.time() + moriarty_move_interval
        else:
            self.next_moriarty_move_time = None

        if moriarty_position != 0:
            self._send_moriarty_move(sio)
        self.debug_game_representation()  # test case debug

        for player in self.players:
            clues = list(map(lambda c: c.to_dict(), player.inventory))
            sio.emit(
                'init',
                {
                    'player_id': player.player_id,
                    'is_mole': player.is_mole,
                    'clues': clues,
                    'rejoin': False,
                    'proofed_types': [],
                },
                room=player.sid
            )

        if got_start_position:
            self.send_to_all(sio, 'move', self.get_team_pos().index)

        self.send_players_turn(sio)

    def send_ping(self, sio):
        sio.emit('ping', '', room=self.desktop_sid)

    def tick(self, sio):
        # check minigame time over
        if self.turn_state.player_turn_state == TurnState.PlayerTurnState.PLAYING_PANTOMINE:
            if self.pantomime_state.is_timeout():
                self.evaluate_pantomime(sio)
        elif self.turn_state.player_turn_state == TurnState.PlayerTurnState.PLAYING_DRAWGAME:
            if self.drawgame_state.is_timeout():
                self.evaluate_drawgame(sio)

        if self.next_moriarty_move_time is not None and self.next_moriarty_move_time < time.time():
            if not self.turn_state.is_in_minigame():
                self.moriarty_move(sio, allow_zero_move=False)

            self.next_moriarty_move_time += self._get_moriarty_move_interval()

        if self.moriarty_hide_time is not None and time.time() - self.moriarty_hide_time > MORIARTY_HIDE_DURATION:
            self.moriarty_hide_time = None
            sio.emit(
                'moriarty_visibility',
                {'visible': True},
                room=self.desktop_sid
            )

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

        player.connected = False
        sio.emit('player_disconnected', player.player_id, room=self.desktop_sid)
        print('player {} disconnected'.format(player.name))

    def player_rejoin(self, sio, sid, name):
        player = self.get_player_by_name(name)
        if player is None:
            print('WARN: got rejoin from player, that could not be found.', file=sys.stderr)
            return

        player.sid = sid
        player.connected = True

        sio.emit('player_rejoined', player.player_id, room=self.desktop_sid)
        player_info = list(map(lambda p: {'name': p.name, 'player_id': p.player_id}, self.players))
        sio.emit('player_infos', player_info, room=player.sid)
        clues = list(map(Clue.to_dict, player.inventory))
        proofed_types = list(map(Proof.to_dict, self._get_all_proofs()))
        sio.emit(
            'init',
            {
                'player_id': player.player_id,
                'is_mole': player.is_mole,
                'map': None,  # TODO: remove this
                'clue': clues[0],  # TODO: remove this
                'clues': clues,
                'rejoin': True,
                'proofed_types': proofed_types,
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
        In case a minigame field is trespassed, the move is stopped.

        :param distance: the number of fields to move
        :return: If a minigame field was reached, the number of remaining move distance is returned, otherwise None
        """
        for i in range(distance):
            self.team_pos = self.team_pos.next  # get next field
            if self.team_pos is None:
                self.game_over(GameOverReason.REACHED_END_OF_MAP)
            else:
                field = self.get_team_pos()
                if field.type == FieldType.MINIGAME and field.game_type == 'pantomime' and self.enable_minigames:
                    return

    def moriarty_move(self, sio, allow_zero_move=True):
        # stop idling
        requests.get("https://ab-backend.herokuapp.com/")

        if allow_zero_move:
            num_fields = random.choices([0, 1, 2], weights=[5, 4, 1])[0]
        else:
            num_fields = random.choices([1, 2], weights=[4, 1])[0]

        if num_fields != 0:
            for i in range(num_fields):
                if self.moriarty_pos.next is None:
                    # TODO: Maybe allow the Team in the future to stall on the goal field to search for evidences
                    self.game_over(GameOverReason.MORIARTY_CAUGHT)
                self.moriarty_pos = self.moriarty_pos.next
                if self.get_moriarty_pos().index == self.get_team_pos().index:
                    self.game_over(GameOverReason.MORIARTY_CAUGHT)

            self._send_moriarty_move(sio)

    def _send_moriarty_move(self, sio):
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
                    room=self.desktop_sid
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

    def get_player_by_id(self, player_id) -> Player or None:
        for player in self.players:
            if player.player_id == player_id:
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
                'type': 'validate-clues',
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
                    room=self.desktop_sid
                )
            elif self.move_modifier == MoveModifier.SIMPLIFY:
                sio.emit(
                    'occasion_info',
                    {'type': 'unsimplify_dicing', 'player_id': self.get_current_player().player_id},
                    room=self.desktop_sid
                )
            self.move_modifier = MoveModifier.NORMAL
            self.handle_movement(sio, move_distance)

        elif player_choice.get('type') == 'share-clue':
            sharing_player = self.get_player(sid)

            # Get player with whom the clue should be shared
            share_with_player = self.get_player_by_id(player_choice.get('with'))
            if share_with_player is None:
                raise InvalidMessageException(
                    'Got player_choice (share-clue), but share_with player_id is invalid:\n\twith: {}'
                    .format(player_choice.get('with'))
                )

            # Get clue which should be shared
            clue = deepcopy(sharing_player.get_clue(player_choice.get('clue')))
            if clue is None:
                raise InvalidMessageException(
                    'Got player_choice (share-clue), with clue name that player does not own'
                    '\n\tclue: {}\n\tinventory: {}'
                    .format(player_choice.get('clue'), sharing_player.inventory)
                )

            # Update sent_to value from players clue
            if share_with_player.player_id not in clue.sent_to:
                clue.sent_to.append(share_with_player.player_id)

            # Check if share_with player already has clue
            share_clue = share_with_player.check_and_add_clue(sharing_player.player_id, clue)

            # Share clue with share_with player
            sio.emit(
                'receive_clue',
                {'clue': share_clue.to_dict()},
                room=share_with_player.sid
            )
            # Send updated clue to player
            clue = clue.to_dict()
            sio.emit(
                'updated_clue',
                {'clue': clue},
                room=sharing_player.sid
            )

            sio.emit(
                'secret_move',
                {'player_id': sharing_player.player_id, 'move_name': 'share-clue'},
                room=self.desktop_sid
            )

            self.end_player_turn(sio)

        elif player_choice.get('type') == 'validate-clues':
            player = self.get_player(sid)
            clues = clues_dict_2_object(player_choice.get('clues'))

            # Validate only when all clues are available. Guessing is not allowed!
            validation_allowed, validation_status = self.validation_allowed(player, clues)
            successful_validation = self.validate_clues(clues) if validation_allowed else False

            # Always send back the clues that should be validated
            if successful_validation:
                validation_status = 'new_validation'
                self.add_verified_clues_to_proofs(clues, player)

            proofed_types = list(map(
                lambda p: {'type': p.main_type, 'from': p.validation_player},
                self._get_all_proofs()
            ))
            self.send_to_all(
                self.sio,
                'validation_result',
                {
                    'successful_validation': successful_validation,
                    'validation_status': validation_status,
                    'player_id': player.player_id,
                    'clues': player_choice.get('clues'),
                    'proofed_types': proofed_types,
                }
            )

            self.end_player_turn(sio)

        elif player_choice.get('type') == 'search-clue':
            player = self.get_player(sid)
            clue = None
            clue2 = None

            if player_choice.get('doublesuccess'):
                clue = self.get_random_missing_clue(player.inventory)
                clue2 = self.get_random_missing_clue(player.inventory)
                # clue can be None, if this player knows everything or every category was validated
                if clue is not None:
                    player.add_clue(-1, clue)
                if clue2 is not None:
                    player.add_clue(-1, clue2)
                else:
                    print('INFO: search-clue, but no clues left to find')

            if player_choice.get('success'):
                clue = self.get_random_missing_clue(player.inventory)
                # clue can be None, if this player knows everything or every category was validated
                if clue is not None:
                    player.add_clue(-1, clue)
                else:
                    print('INFO: search-clue, but no clues left to find')

            if clue is not None:
                sio.emit(
                    'receive_clue',
                    {'clue': clue.to_dict()},
                    room=player.sid
                )

            if clue2 is not None:
                sio.emit(
                    'receive_clue',
                    {'clue': clue2.to_dict()},
                    room=player.sid
                )
            sio.emit(
                'secret_move',
                {'player_id': player.player_id, 'move_name': 'search-clue'},
                room=self.desktop_sid
            )

            self.end_player_turn(sio)

    def handle_movement(self, sio, move_distance: int):
        """
        Moves the player while handling turn state, minigames and occasions.
        """
        if move_distance == 0:
            self.send_to_all(sio, 'move', self.get_team_pos().index)  # send 0 move event
            self.end_player_turn(sio)
            return
        self.move_player(move_distance)
        self.send_to_all(sio, 'move', self.get_team_pos().index)

        if self.get_team_pos().type is FieldType.MINIGAME:
            print("stepped on shortcut, index:" + str(self.get_team_pos().index))
            if self.get_team_pos().game_type == 'pantomime':
                self.turn_state.player_turn_state = TurnState.PlayerTurnState.PLAYING_PANTOMINE
                self.trigger_pantomime(sio, self.get_team_pos().difficulty)
            elif self.get_team_pos().game_type == 'drawgame':
                self.turn_state.player_turn_state = TurnState.PlayerTurnState.PLAYING_DRAWGAME
                self.trigger_drawgame(sio, self.get_team_pos().difficulty)
            
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

        sio.emit('occasion_info', chosen_occasion, room=self.desktop_sid)

        if occasion_type == 'found_clue':
            player = self.get_player(sid)

            if chosen_occasion.get('success') is True:
                clue = self.get_random_missing_clue(player.inventory)
                if clue is not None:
                    player.add_clue(-1, clue)
                    clue = clue.to_dict()

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

    def _get_drawgame_category(self, difficulty):
        usages = self.drawgame_category_count[difficulty]
        usages = sorted(usages.items(), key=lambda u: u[1])
        lowest_usage = usages[0][1]
        usages = filter(lambda u: u[1] == lowest_usage, usages)
        category = random.choice(list(usages))[0]
        return category

    def trigger_pantomime(self, sio, difficulty):
        category = self._get_pantomime_category(difficulty)
        words = random.choice(PANTOMIME_WORDS[difficulty][category])
        self.pantomime_category_count[difficulty][category] += 1

        solution_word = random.choice(words)
        self.pantomime_state = PantomimeState(solution_word, words, category)

        # inform host
        sio.emit(
            'guess_pantomime',
            {
                'words': words,
                'category': category,
                'start': False,
                'ignored': False,
            },
            room=self.desktop_sid
        )
        for player in self.players:
            if player.sid == self.get_current_player().sid:
                sio.emit(
                    'host_pantomime',
                    {'solution_word': solution_word, 'words': words, 'category': category},
                    room=player.sid
                )
            else:
                sio.emit(
                    'guess_pantomime',
                    {
                        'words': words,
                        'category': category,
                        'start': False,
                        'ignored': False,
                    },
                    room=player.sid
                )

    def trigger_drawgame(self, sio, difficulty):
        print('trigger drawgame')
        category = self._get_drawgame_category(difficulty)
        words = random.choice(DRAWGAME_WORDS[difficulty][category])
        self.drawgame_category_count[difficulty][category] += 1

        solution_word = random.choice(words)
        self.drawgame_state = DrawgameState(solution_word, words, category)

        # inform host
        sio.emit(
            'guess_drawgame',
            {
                'words': words,
                'category': category,
                'start': False,
                'ignored': False,
            },
            room=self.desktop_sid
        )
        for player in self.players:
            if player.sid == self.get_current_player().sid:
                sio.emit(
                    'host_drawgame',
                    {'solution_word': solution_word, 'words': words, 'category': category},
                    room=player.sid
                )
            else:
                sio.emit(
                    'guess_drawgame',
                    {
                        'words': words,
                        'category': category,
                        'start': False,
                        'ignored': False,
                    },
                    room=player.sid
                )

    def pantomime_start(self, sio, sid, ignored_player):
        # check if in pantomime
        if not self.turn_state.player_turn_state == TurnState.PlayerTurnState.PLAYING_PANTOMINE:
            raise InvalidMessageException('Got pantomime start, but not in minigame\n\tsid: {}'.format(sid))
        if self.pantomime_state is None:
            raise AssertionError('pantomime_state is None in minigame')

        # get player
        hosting_player = self.get_player(sid)
        if hosting_player is None:
            raise InvalidMessageException('Could not find player with sid: {}'.format(sid))
        if hosting_player.sid != self.get_current_player().sid:
            raise InvalidMessageException('Got pantomime start from player that is not hosting.')

        self.pantomime_state.start_timeout()

        # ignore player
        if hosting_player.player_id == ignored_player:  # hosting player can not ignore himself
            print('WARN: hosting player tried to ignore himself', file=sys.stderr)
        else:
            if ignored_player is not None:
                if ignored_player not in map(lambda p: p.player_id, self.players):  # catch unknown player
                    print('WARN: unknown ignored player id: {}'.format(ignored_player))
                else:
                    self.pantomime_state.ignored_player = ignored_player

        for hosting_player in self.players:
            if hosting_player.sid != self.get_current_player().sid:
                sio.emit(
                    'guess_pantomime',
                    {
                        'words': self.pantomime_state.words,
                        'category': self.pantomime_state.category,
                        'start': True,
                        'ignored': hosting_player.player_id == ignored_player,
                    },
                    room=hosting_player.sid
                )

    def drawgame_start(self, sio, sid, ignored_player):
        print('starting drawgame')
        # check if in drawgame
        if not self.turn_state.player_turn_state == TurnState.PlayerTurnState.PLAYING_DRAWGAME:
            raise InvalidMessageException('Got drawgame start, but not in minigame\n\tsid: {}'.format(sid))
        if self.drawgame_state is None:
            raise AssertionError('drawgame_state is None in minigame')

        # get player
        hosting_player = self.get_player(sid)
        if hosting_player is None:
            raise InvalidMessageException('Could not find player with sid: {}'.format(sid))
        if hosting_player.sid != self.get_current_player().sid:
            raise InvalidMessageException('Got drawgame start from player that is not hosting.')

        self.drawgame_state.start_timeout()

        # ignore player
        if hosting_player.player_id == ignored_player:  # hosting player can not ignore himself
            print('WARN: hosting player tried to ignore himself', file=sys.stderr)
        else:
            if ignored_player is not None:
                if ignored_player not in map(lambda p: p.player_id, self.players):  # catch unknown player
                    print('WARN: unknown ignored player id: {}'.format(ignored_player))
                else:
                    self.drawgame_state.ignored_player = ignored_player

        for hosting_player in self.players:
            if hosting_player.sid != self.get_current_player().sid:
                sio.emit(
                    'guess_drawgame',
                    {
                        'words': self.drawgame_state.words,
                        'category': self.drawgame_state.category,
                        'start': True,
                        'ignored': hosting_player.player_id == ignored_player,
                    },
                    room=hosting_player.sid
                )

        print('desktop start drawgame: self.desktop_sid={}'.format(self.desktop_sid))
        sio.emit(
            'desktop_start_drawgame',
            {
                'drawing_player_name': hosting_player.name,
            },
            room=self.desktop_sid
        )

    def pantomime_choice(self, sio, sid, message):
        # check if in pantomime
        if not self.turn_state.player_turn_state == TurnState.PlayerTurnState.PLAYING_PANTOMINE:
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
        if player.player_id == self.pantomime_state.ignored_player:
            print('WARN: got guess from ignored player', file=sys.stderr)
            return

        self.pantomime_state.guesses[player.player_id] = guess

        # evaluate, if everyone has answered
        num_players_to_guess = len(self.players) - 1
        if self.pantomime_state.ignored_player is not None:
            num_players_to_guess -= 1
        if len(self.pantomime_state.guesses) == num_players_to_guess:
            self.evaluate_pantomime(sio)

    def drawgame_choice(self, sio, sid, message):
        # check if in drawgame
        if not self.turn_state.player_turn_state == TurnState.PlayerTurnState.PLAYING_DRAWGAME:
            raise InvalidMessageException('Got drawgame choice, but not in minigame\n\tsid: {}'.format(sid))
        if self.drawgame_state is None:
            raise AssertionError('drawgame_state is None in minigame')
        if not self.drawgame_state.timeout_started():
            raise InvalidMessageException('game has not started, but got drawgame choice')

        # get player
        player = self.get_player(sid)
        if player is None:
            raise InvalidMessageException('Could not find player with sid: {}'.format(sid))
        if player.sid == self.get_current_player().sid:
            raise InvalidMessageException('Got drawgame choice from hosting player.')

        # validate message
        if not isinstance(message, dict):
            raise InvalidMessageException('Got drawgame choice, but message is no dictionary')
        guess = message.get('guess')
        if guess is None:
            raise InvalidMessageException(
                'Got drawgame choice without key "guess". Message keys: {}'.format(message.keys())
            )
        if guess not in self.drawgame_state.words:
            raise InvalidMessageException(
                'Got invalid guess "{}". Not in possible words: {}'.format(guess, self.drawgame_state.words)
            )
        if player.player_id == self.drawgame_state.ignored_player:
            print('WARN: got guess from ignored player', file=sys.stderr)
            return

        self.drawgame_state.guesses[player.player_id] = guess

        # evaluate, if everyone has answered
        num_players_to_guess = len(self.players) - 1
        if self.drawgame_state.ignored_player is not None:
            num_players_to_guess -= 1
        if len(self.drawgame_state.guesses) == num_players_to_guess:
            self.evaluate_drawgame(sio)

    def evaluate_pantomime(self, sio):
        player_results = []
        overall_success = True
        for player in self.players:
            # skip disconnected players and host player
            if not player.connected or player.sid == self.get_current_player().sid:
                continue
            # handle ignored player
            if player.player_id == self.pantomime_state.ignored_player:
                player_results.append({
                    'player_id': player.player_id,
                    'success': True,
                    'guess': None,
                    'ignored': True,
                })
                continue
            player_guess = self.pantomime_state.guesses.get(player.player_id)
            success = player_guess == self.pantomime_state.solution_word
            if not success:
                overall_success = False
            player_results.append({
                'player_id': player.player_id,
                'success': success,
                'guess': player_guess,
                'ignored': False,
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
            move_distance = team_pos.shortcut_field - team_pos.index
            self.handle_movement(sio, move_distance)
        else:
            self.end_player_turn(sio)

    def evaluate_drawgame(self, sio):
        player_results = []
        overall_success = True
        for player in self.players:
            # skip disconnected players and host player
            if not player.connected or player.sid == self.get_current_player().sid:
                continue
            # handle ignored player
            if player.player_id == self.drawgame_state.ignored_player:
                player_results.append({
                    'player_id': player.player_id,
                    'success': True,
                    'guess': None,
                    'ignored': True,
                })
            else:
                player_guess = self.drawgame_state.guesses.get(player.player_id)
                success = player_guess == self.drawgame_state.solution_word
                if not success:
                    overall_success = False
                player_results.append({
                    'player_id': player.player_id,
                    'success': success,
                    'guess': player_guess,
                    'ignored': False,
                })

        message = {
            'success': overall_success,
            'player_results': player_results,
            'solution_word': self.drawgame_state.solution_word
        }

        self.send_to_all(sio, 'drawgame_result', message)

        self.drawgame_state = None
        if overall_success:
            player = self.get_current_player()
            clue = self.get_random_missing_clue(player.inventory)
            # clue can be None, if this player knows everything or every category was validated
            if clue is not None:
                player.add_clue(-1, clue)
                sio.emit(
                    'receive_clue',
                    {'clue': clue.to_dict()},
                    room=player.sid
                )
            else:
                print('INFO: evaluate-drawgame, but no clues left to find')
        else:
            sio.emit(
                'moriarty_visibility',
                {'visible': False},
                room=self.desktop_sid
            )
            self.moriarty_hide_time = time.time()

        self.end_player_turn(sio)

    def forward_drawgame_data(self, sio, sid, message):
        """
        Forwards drawgame data to host.
        """
        if not self.turn_state.player_turn_state == TurnState.PlayerTurnState.PLAYING_DRAWGAME:
            raise InvalidMessageException('Got drawgame data, but not in drawgame\n\tsid: {}'.format(sid))
        if self.drawgame_state is None:
            raise AssertionError('drawgame_state is None in drawgame')
        if not self.drawgame_state.timeout_started():
            raise InvalidMessageException('game has not started, but got drawgame choice')

        # get player
        player = self.get_player(sid)
        if player is None:
            raise InvalidMessageException('Could not find player with sid: {}'.format(sid))
        if player.sid != self.get_current_player().sid:
            raise InvalidMessageException('Got drawgame update from not hosting player.')

        sio.emit('drawgame_update', message, room=self.desktop_sid)

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

    def _player_has_clue(self, clue_name):
        for player in self.players:
            if player.get_clue(clue_name) is not None:
                return True
        return False

    def get_random_missing_clue(self, player_clues: List[Clue]) -> Clue or None:
        """
        :param player_clues: The clues the player already has
        :return: Get a random clue, which the player does not have yet and whose main type was not validated yet.
                 None, if there is no such clue
        """
        def _valid_found_clue(find_clue) -> bool:
            """
            Returns whether this clue should be findable.
            It is not findable anymore, if it is already verified.
            It is not findable anymore, if the player has this clue already.

            :param find_clue: The clue to inspect
            :type find_clue: Clue
            :return: True or False
            """
            # already verified
            if self.is_already_verified(find_clue.main_type):
                return False

            if find_clue.name in map(lambda pc: pc.name, player_clues):
                return False

            return True

        possible_clues = list(filter(_valid_found_clue, self.solution_clues))

        weighted_possible_clues = []
        for clue in possible_clues:
            weighted_possible_clues.append(clue)
            if not self._player_has_clue(clue.name):
                for _ in range(3):
                    weighted_possible_clues.append(clue)

        if len(weighted_possible_clues) == 0:
            return None

        return deepcopy(random.choice(weighted_possible_clues))

    def get_clue_by_name(self, clue_name: str):
        for c in self.solution_clues:
            if c.name == clue_name:
                return c

    def validation_allowed(self, player: Player, clues: List[Clue]) -> (bool, str):
        """
        Checks whether the given clues are in the players inventory.

        :param player: The player that wants to validate
        :param clues: The list of clues to validate
        :return: A tuple (success, msg), where success is a bool and msg describes the reasoning behind errors
        """
        clue_type = clues[0].main_type

        for clue in clues:
            # The clue type must be the same for all clues
            if clue.main_type != clue_type:
                raise InvalidMessageException('Got different clue main_types which is illegal')

            # The clues must be in the players inventory
            if player.get_clue(clue.name) is None:
                return False, 'not_in_inventory'

        # Check if the clues have already been verified
        if self.is_already_verified(clue_type):
            return False, 'already_verified'
        else:
            return True, 'validation_allowed'

    def _get_all_proofs(self) -> List[Proof]:
        return list(itertools.chain(self.team_proofs, self.mole_proofs))

    def is_already_verified(self, main_type: str) -> bool:
        # Check if the verified clues have already been added to the other teams proofs or self proofs
        return main_type in map(lambda p: p.main_type, self._get_all_proofs())

    def validate_clues(self, clues):
        """
        :rtype: Bool
        :return: Bool whether the correct clues were found or not
        """
        clue_type = clues[0].main_type
        clue_group = []

        # Get all winner clues with requested clue type
        for clue in self.solution_clues:
            if clue.main_type == clue_type:
                clue_group.append(clue)

        # Check if player has all the clues needed
        for clue in clues:
            if clue.main_type != clue_type:
                return False

            result = next((e for e in clue_group if e.name == clue.name), None)
            if result is not None:
                clue_group.remove(result)

        return len(clue_group) == 0

    def add_verified_clues_to_proofs(self, clues, player: Player):
        main_type = clues[0].main_type
        proof = Proof(main_type, player.player_id)
        if player.is_mole:
            self.mole_proofs.append(proof)
        else:
            self.team_proofs.append(proof)

    def generate_solution_clues(self) -> List[Clue]:
        """
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
        clues.append(evidence_2_clue(random.choice(all_weapon_objects)))
        clues.append(evidence_2_clue(random.choice(all_weapon_colors)))
        clues.append(evidence_2_clue(random.choice(all_weapon_conditions)))

        all_crime_scene_locations = Evidence.objects.using(db_connection).filter(type=ClueType.CRIME_SCENE,
                                                                                 subtype=ClueSubtype.LOCATION)
        all_crime_scene_temperature = Evidence.objects.using(db_connection).filter(type=ClueType.CRIME_SCENE,
                                                                                   subtype=ClueSubtype.TEMPERATURE)
        all_crime_scene_districts = Evidence.objects.using(db_connection).filter(type=ClueType.CRIME_SCENE,
                                                                                 subtype=ClueSubtype.DISTRICT)
        clues.append(evidence_2_clue(random.choice(all_crime_scene_locations)))
        clues.append(evidence_2_clue(random.choice(all_crime_scene_temperature)))
        clues.append(evidence_2_clue(random.choice(all_crime_scene_districts)))

        all_offender_escape_clothings = Evidence.objects.using(db_connection).filter(type=ClueType.OFFENDER,
                                                                                     subtype=ClueSubtype.CLOTHING)
        all_offender_escape_sizes = Evidence.objects.using(db_connection).filter(type=ClueType.OFFENDER,
                                                                                 subtype=ClueSubtype.SIZE)
        all_offender_escape_characteristics = Evidence.objects.using(db_connection)\
            .filter(type=ClueType.OFFENDER, subtype=ClueSubtype.CHARACTERISTIC)
        clues.append(evidence_2_clue(random.choice(all_offender_escape_clothings)))
        clues.append(evidence_2_clue(random.choice(all_offender_escape_sizes)))
        clues.append(evidence_2_clue(random.choice(all_offender_escape_characteristics)))

        all_time_of_crime_weekdays = Evidence.objects.using(db_connection).filter(type=ClueType.TIME_OF_CRIME,
                                                                                  subtype=ClueSubtype.WEEKDAY)
        all_time_of_crime_daytimes = Evidence.objects.using(db_connection).filter(type=ClueType.TIME_OF_CRIME,
                                                                                  subtype=ClueSubtype.DAYTIME)
        all_time_of_crime_times = Evidence.objects.using(db_connection).filter(type=ClueType.TIME_OF_CRIME,
                                                                               subtype=ClueSubtype.TIME)
        clues.append(evidence_2_clue(random.choice(all_time_of_crime_weekdays)))
        clues.append(evidence_2_clue(random.choice(all_time_of_crime_daytimes)))
        clues.append(evidence_2_clue(random.choice(all_time_of_crime_times)))

        all_mean_of_escape_conditions = Evidence.objects.using(db_connection).filter(type=ClueType.MEANS_OF_ESCAPE,
                                                                                     subtype=ClueSubtype.MODEL)
        all_mean_of_escape_daytime = Evidence.objects.using(db_connection).filter(type=ClueType.MEANS_OF_ESCAPE,
                                                                                  subtype=ClueSubtype.COLOR_ME)
        all_mean_of_escape_districts = Evidence.objects.using(db_connection).filter(type=ClueType.MEANS_OF_ESCAPE,
                                                                                    subtype=ClueSubtype.ESCAPE_ROUTE)
        clues.append(evidence_2_clue(random.choice(all_mean_of_escape_conditions)))
        clues.append(evidence_2_clue(random.choice(all_mean_of_escape_daytime)))
        clues.append(evidence_2_clue(random.choice(all_mean_of_escape_districts)))

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

            # Mole wins if he has verified at least two proofs (Reminder: proof is now single object)
            if len(self.mole_proofs) >= 2:
                message = "destroyed_enough_proofs"
            # Team wins if it has verified at least four proofs (Reminder: proof is now single object)
            elif len(self.team_proofs) >= 4:
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

    def _get_moriarty_move_interval(self):
        value = random.random() * (MORIARTY_AUTO_MOVE_INTERVAL[1] - MORIARTY_AUTO_MOVE_INTERVAL[0]) + \
               MORIARTY_AUTO_MOVE_INTERVAL[0]
        if self.difficulty == DifficultyLevel.EASY:
            return None
        elif self.difficulty == DifficultyLevel.MEDIUM:
            return value * 2.0
        elif self.difficulty == DifficultyLevel.HARD:
            return value


def _occasion_matches(left, right):
    if left['type'] != right['type']:
        return False
    if left['type'] == 'move_forwards':
        if left['value'] != right['value']:
            return False
    return True


class InvalidMessageException(Exception):
    pass

