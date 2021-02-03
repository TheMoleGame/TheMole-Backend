import time


PANTOMIME_DURATION = 30

PANTOMIME_WORDS = [
    ('escape_route', ['wide_canal', 'wide_street', 'dark_canal', 'dark_street']),
    ('escape_vehicle', ['long_boat', 'long_train', 'fast_boat', 'fast_train']),
    ('danger', ['spiky_wire_fence', 'hidden_trap_door', 'open_laces', 'glass_lying_around']),
    ('approach', ['creep_quiet', 'crawl_flat', 'climb_fast', 'run_fast']),
    ('discovery', ['left_behind_note', 'valid_ticket', 'hidden_shortcut', 'lost_letter']),
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
