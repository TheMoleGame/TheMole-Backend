from typing import List, Dict
from copy import deepcopy

from mole.models import Evidence


class Clue:
    def __init__(self, name, main_type, subtype, received_from=-1, sent_to=None):
        self.name = name
        self.main_type = main_type
        self.subtype = subtype
        self.received_from = received_from
        self.sent_to = []

        if sent_to is not None:
            self.sent_to.append(sent_to)

    def __eq__(self, other):
        if not isinstance(other, Clue):
            return False
        if self is other:
            return True
        return self.name == other.name and self.main_type == other.main_type and self.subtype == other.subtype

    def to_dict(self):
        d = deepcopy(self.__dict__)
        d['type'] = d['main_type']
        del d['main_type']
        return d


class Proof:
    def __init__(self, main_type, validation_player):
        self.main_type = main_type
        self.validation_player = validation_player

    def to_dict(self):
        return {'type': self.main_type, 'from': self.validation_player}


def evidence_2_clue(evidence: Evidence) -> Clue:
    """
    Converts an evidence object into a clue.

    :param evidence: The evidence to convert
    """
    return Clue(name=evidence.name, main_type=evidence.type, subtype=evidence.subtype)


def clues_dict_2_object(clues: List[Dict[str, str]]) -> List[Clue]:
    """
    Converts a list of dictionaries with clue information into a list of clues

    :return: Converted clues
    """
    converted_clues = []

    for clue in clues:
        converted_clues.append(Clue(name=clue['name'], main_type=clue['type'], subtype=clue['subtype']))

    return converted_clues
