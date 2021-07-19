import time


DRAWGAME_DURATION = 60

# TODO: rework words
DRAWGAME_WORDS = {
    'easy': {
        'escape_route': [
            ['wide_canal', 'wide_street', 'dark_canal', 'dark_street'],
            # ['dense_forest', 'dense_bushes', 'light_forest', 'light_bushes'],
            # ['small_way', 'small_path', 'big_way', 'big_path'],
            # ['dark_cave', 'dark_tunnel', 'scary_cave', 'scary_tunnel'],
        ],
        'escape_vehicle': [
            ['long_boat', 'long_train', 'fast_boat', 'fast_train'],
            ['old_unicycle', 'old_bicycle', 'new_unicycle', 'new_bicycle'],
            # ['big_hot_air_balloon', 'small_hot_air_balloon', 'big_zeppelin', 'small_zeppelin'],
        ],
        'approach': [
            ['comfortable_driving', 'safe_flying', 'brisk_walking', 'fast_sliding'],
            ['creep_quiet', 'crawl_flat', 'climb_fast', 'run_fast'],
            # ['black_horse', 'white_horse', 'black_donkey', 'white_donkey'],
        ]
    },
    'medium': {
        'danger': [
            ['heavy_hammer', 'hard_pickaxe', 'long_machete', 'sharp_knife'],
            ['obstructed_path', 'enraged_mob', 'cunning_assassin', 'impenetrable_assembly'],
        ],
        'escape_route': [
            ['old_door', 'old_gate', 'decorated_door', 'decorated_gate'],
        ],
        'escape_vehicle': [
            ['expensive_carriage', 'narrow_carriage', 'expensive_carry', 'narrow_carry']
        ]
    },
    'hard': {
        'danger': [
            ['spiky_wire_fence', 'hidden_trap_door', 'open_laces', 'glass_lying_around'],
            ['loud_pistol', 'quiet_silencer', 'dangerous_murderer', 'scary_follower'],
            ['nasty_traitor', 'eavesdropping_snitch', 'secret_pursuer', 'stupid_agent'],
        ],
        'discovery': [
            ['left_behind_note', 'valid_ticket', 'hidden_shortcut', 'lost_letter'],
            ['hidden_postcard', 'conspicuous_sign', 'locked_chest', 'inconspicuous_secret_door'],
            ['bushy_shelter', 'high_lookout', 'small_trench', 'secret_hiding_place'],
            ['inconspicuous_clue', 'public_evidence', 'interesting_information', 'false_trail'],
            ['big_magnifying_glass', 'long_binoculars', 'matching_monocle', 'broken_glasses'],
        ],
    }
}


def _get_time():
    return time.monotonic()


class DrawgameState:
    def __init__(self, solution_word, words, category):
        self.solution_word = solution_word
        self.words = words
        self.category = category
        self.guesses = {}  # maps player_id to guess
        self.start_time = None
        self.ignored_player = None

    def start_timeout(self):
        self.start_time = _get_time()

    def is_timeout(self):
        return self.timeout_started() and _get_time() > self.start_time + DRAWGAME_DURATION

    def timeout_started(self):
        return self.start_time is not None
