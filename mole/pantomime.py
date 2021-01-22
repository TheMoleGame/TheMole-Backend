import time


PANTOMIME_DURATION = 60.0 * 1.0  # one minute

# TODO: create more pantomime categories
PANTOMIME_WORDS = [
    ('escape_route', ['grotty_canal', 'bright_way', 'cold_street', 'small_path']),
    # ('escape_vehicle', ['long_boat', 'goofy_unicycle', 'cute_carriage', 'fancy_sled']),
]


class PantomimeState:
    def __init__(self, solution_word, words):
        self.solution_word = solution_word
        self.words = words
        self.guesses = {}  # maps player_id to guess
        self.start_time = time.time()
