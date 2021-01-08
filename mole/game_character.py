from abc import ABCMeta, abstractmethod
from typing import List

from mole.models import Evidence


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

    def __init__(self, player_id, name, sid, evidence=None, is_mole=False):
        self.player_id = player_id
        self._name = name
        self.is_mole = is_mole

        self.inventory = []  # type: List[Evidence]
        if evidence is not None:
            self.inventory.append(evidence)

        self.sid = sid
        self.disabled = False

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


