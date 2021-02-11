from typing import List

from mole.clues import Clue


class Player:
    @property
    def name(self):
        return self._name

    def __init__(self, player_id, name, sid, clue=None, is_mole: bool = False):
        self.player_id = player_id
        self._name = name
        self.is_mole = is_mole

        self.inventory = []  # type: List[Clue]
        if clue is not None:
            self.inventory.append(clue)

        self.sid = sid
        self.disabled = False
        self.connected = True

    def add_clue(self, received_from: int, clue: Clue):
        # Reset received_from and sent_to information
        clue_copy = Clue(name=clue.name, main_type=clue.main_type, subtype=clue.subtype, received_from=received_from)

        self.inventory.append(clue_copy)
        return clue_copy

    def check_and_add_clue(self, received_from, clue):
        """
        This does not add the given clue to the inventory, if the player already has this clue.

        :param received_from:
        :param clue:
        :return:
        """
        c = self.get_clue(clue.name)
        if c is not None:
            return c

        return self.add_clue(received_from, clue)

    def get_clue(self, name):
        for c in self.inventory:
            if c.name == name:
                return c
        return None
