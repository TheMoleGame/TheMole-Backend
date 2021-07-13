from enum import Enum
import pyllist


class FieldType(str, Enum):
    WALKABLE = 'walkable'
    OCCASION = 'occasion'
    DEVIL_FIELD = 'devil_field'
    SHORTCUT = 'shortcut'
    Goal = 'goal'


class Field(dict):
    counter = 0

    def __init__(self, field_type=FieldType.WALKABLE, shortcut_field=None, difficulty=None, game_type=None):
        if field_type == FieldType.SHORTCUT and difficulty is None:
            raise AssertionError('cant create SHORTCUT without difficulty level')
        dict.__init__(self, index=Field.counter)
        self.index = Field.counter
        Field.counter = Field.counter + 1
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
    map_dll.append(Field(FieldType.SHORTCUT, 10, 'easy', 'drawgame'))  # was Minigame
    map_dll.append(Field(FieldType.WALKABLE))
    map_dll.append(Field(FieldType.OCCASION))
    map_dll.append(Field(FieldType.OCCASION))
    map_dll.append(Field(FieldType.SHORTCUT, 18, 'easy', 'pantomime'))  # id == 14
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
    map_dll.append(Field(FieldType.SHORTCUT, 33, 'easy', 'pantomime'))
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
    map_dll.append(Field(FieldType.SHORTCUT, 42, 'medium', 'pantomime'))
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
    map_dll.append(Field(FieldType.SHORTCUT, 57, 'medium', 'pantomime'))
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
    map_dll.append(Field(FieldType.SHORTCUT, 83, 'hard', 'pantomime'))
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

    return map_dll
