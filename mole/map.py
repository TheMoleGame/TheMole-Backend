from enum import Enum
import pyllist
import random


DRAWGAME_PROBABILITY = 0.1


class FieldType(str, Enum):
    WALKABLE = 'walkable'
    OCCASION = 'occasion'
    DEVIL_FIELD = 'devil_field'
    MINIGAME = 'minigame'
    Goal = 'goal'


class Field(dict):
    def __init__(self, field_type=FieldType.WALKABLE, shortcut_field=None, difficulty=None, game_type=None):
        if field_type == FieldType.MINIGAME and difficulty is None:
            raise AssertionError('cant create SHORTCUT without difficulty level')
        dict.__init__(self)
        self.index = -1
        self.shortcut_field = shortcut_field    # int
        self.difficulty = difficulty
        self.type = field_type                  # type: FieldType
        self.game_type = game_type                 
        dict.__setitem__(self, "shortcut", self.shortcut_field)
        dict.__setitem__(self, "field_type", self.type)


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
    map_dll.append(Field(FieldType.MINIGAME, 10, 'easy', 'drawgame'))  # was Minigame
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.OCCASION))
    map_dll.append(Field(FieldType.OCCASION))
    map_dll.append(Field(FieldType.MINIGAME, 18, 'easy', 'pantomime'))  # id == 14
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
    map_dll.append(Field(FieldType.MINIGAME, 33, 'easy', 'pantomime'))
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
    map_dll.append(Field(FieldType.MINIGAME, 42, 'medium', 'pantomime'))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.OCCASION))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.OCCASION))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.MINIGAME, 57, 'medium', 'pantomime'))
    map_dll.append(Field(FieldType.OCCASION))
    map_dll.append(Field(FieldType.OCCASION))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.OCCASION))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.OCCASION))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.OCCASION))
    map_dll.append(Field(FieldType.OCCASION))
    map_dll.append(Field(FieldType.OCCASION))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.OCCASION))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.MINIGAME, 83, 'hard', 'pantomime'))
    map_dll.append(Field(FieldType.OCCASION))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.OCCASION))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.OCCASION))
    map_dll.append(Field(FieldType.OCCASION))
    map_dll.append(Field(FieldType.OCCASION))
    map_dll.append(Field(FieldType.Goal))

    map_len = len(map_dll)

    for field_index, field in enumerate(map_dll):
        if field.type == FieldType.WALKABLE and random.random() < DRAWGAME_PROBABILITY:
            if field_index < map_len/3:
                difficulty = 'easy'
            elif field_index < map_len/3*2:
                difficulty = 'medium'
            else:
                difficulty = 'hard'

            map_dll[field_index] = Field(FieldType.MINIGAME, 0, difficulty, 'drawgame')

        map_dll[field_index].index = field_index

    return map_dll
