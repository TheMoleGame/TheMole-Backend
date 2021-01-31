import time


PANTOMIME_DURATION = 30

# TODO: create more pantomime categories
PANTOMIME_WORDS = [
    ('escape_route', ['grotty_canal', 'bright_way', 'cold_street', 'small_path']),
    ('escape_vehicle', ['long_boat', 'goofy_unicycle', 'clean_carriage', 'fancy_sled']),
]


def _get_time():
    return time.monotonic()


class PantomimeState:
    def __init__(self, solution_word, words, category):
        self.solution_word = solution_word
        self.words = words
        self.category = category
        self.guesses = {}  # maps player_id to guess
        self.start_time = None

    def start_timeout(self):
        self.start_time = _get_time()

    def is_timeout(self):
        return self.timeout_started() and _get_time() > self.start_time + PANTOMIME_DURATION

    def timeout_started(self):
        return self.start_time is not None
