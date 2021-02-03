from abc import ABCMeta, abstractmethod
from typing import List

from .models import Clue


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

    def __init__(self, player_id, name, sid, clue=None, is_mole=False):
        self.player_id = player_id
        self._name = name
        self.is_mole = is_mole

        self.inventory = []  # type: List[Clue]
        if clue is not None:
            self.inventory.append(clue)

        self.sid = sid
        self.disabled = False
        self.connected = True

    def add_clue(self, received_from, clue):
        # Reset received_from and sent_to information
        clue_copy = Clue(name=clue.name, type=clue.type, subtype=clue.subtype, received_from=received_from)

        self.inventory.append(clue_copy)
        return clue_copy

    def check_and_add_clue(self, received_from, clue):
        for c in self.inventory:
            if c.name == clue.name:
                return c

        return self.add_clue(received_from, clue)

    def search_hint(self) -> []:
        # TODO
        pass

    def share_hint(self, hint):
        # TODO
        pass

    def generate_occasion(self) -> int:
        # TODO
        pass

    def validate(self, evidence):
        if evidence is True:
            return True
        return False


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


