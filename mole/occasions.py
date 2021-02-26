import random

OCCASIONS = ['found_clue', 'move_forwards', 'simplify_dicing', 'skip_player', 'hinder_dicing']


def _random_occasion_choices(test_choices=None):
    choices = []

    if test_choices is not None and len(test_choices) >= 1 and test_choices[0] is not None:
        # Add first test choice
        choices.append(test_choices[0])

        if len(test_choices) == 1:
            # Add random choice
            choices_copy = OCCASIONS.copy()
            choices_copy.remove(test_choices[0])
            choices.append(random.choice(choices_copy))

        elif len(test_choices) == 2 and test_choices[1] is not None:
            # Add second test choice
            choices.append(test_choices[1])
    else:
        # Add random choices
        choices = random.sample(OCCASIONS, 2)

    def _enrich_choice(choice):
        result = {'type': choice}
        if choice == 'move_forwards':
            result['value'] = random.randint(1, 4)
        elif choice == 'skip_player':
            result['name'] = None
        return result

    return list(map(_enrich_choice, choices))

