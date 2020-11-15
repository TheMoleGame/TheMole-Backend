from abc import ABCMeta, abstractmethod

import pyllist

from mole.game import Game


class CharacterInterface(metaclass=ABCMeta):
    @property
    @abstractmethod
    def name(self):
        raise NotImplementedError

    @abstractmethod
    def generate_occasion(self) -> int:
        raise NotImplementedError


class Player(CharacterInterface):
    @property
    def name(self):
        return self._name

    def __init__(self, name, sid, is_mole=False):
        self._name = name
        self.is_mole = is_mole
        self.inventory = []
        self.sid = sid

    def search_hint(self) -> []:
        # TODO
        pass

    def share_hint(self, hint):
        # TODO
        pass

    def generate_occasion(self) -> int:
        # TODO
        pass

    def validate(evidence):
        if evidence is True:
            return True
        return False

    def move(self, game: Game, distance) :
        game.team_pos: pyllist.dllist

        #  for i in range(0, distance):
            #  team_pos.has_Team = False
            #  team_pos. = team_pos.next_field
            #  team_pos.has_Team = False
        pass


class Devil(CharacterInterface):
    @property
    def name(self):
        return self._name

    def __init__(self, name):
        self._name = name
        self.distance_to_team = 3 # ? to define

    def generate_occasion(self) -> int:
        # TODO
        # speed_up as option
        pass


