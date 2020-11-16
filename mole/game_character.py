from abc import ABCMeta, abstractmethod

import pyllist

from mole.game import *


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

    def move(self, position: pyllist.dllistnode, distance):
        for i in range(0, distance):
            field: Field = position.value
            field.set_has_team(False)
            next_pos: pyllist.dllistnode = position.next()
            field: Field = next_pos.value
            field.set_has_team(True)
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


