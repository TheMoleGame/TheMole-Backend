from .models import EventField, EventFieldType, Clue, ClueSubtype, ClueType, MimePair, WouldYouRatherPair


def create_event_fields():
    event_fields = [
        EventField(name='Hinweis suchen', description='', occasion_type=EventFieldType.OCCASION),
        EventField(name='X Felder vor', description='', occasion_type=EventFieldType.OCCASION),
        EventField(name='Würfeln erleichtern', description='', occasion_type=EventFieldType.OCCASION),
        EventField(name='Aussetzen von gewählten Personen', description='', occasion_type=EventFieldType.OCCASION),
        EventField(name='X Felder zurück', description='', occasion_type=EventFieldType.OCCASION),
        EventField(name='Würfeln erschweren', description='', occasion_type=EventFieldType.OCCASION),

        EventField(name='The Trust Game', description='', occasion_type=EventFieldType.MINIGAME),
        EventField(name='The Silence Game', description='', occasion_type=EventFieldType.MINIGAME),
        EventField(name='The Lock Picking Game', description='', occasion_type=EventFieldType.MINIGAME)

    ]
    for field in event_fields:
        field.save()
    pass


def create_weapons():
    weapons = [
        # Object
        Clue(name='Messer', type=ClueType.WEAPON, subtype=ClueSubtype.OBJECT),
        Clue(name='Axt', type=ClueType.WEAPON, subtype=ClueSubtype.OBJECT),
        Clue(name='Pistole', type=ClueType.WEAPON, subtype=ClueSubtype.OBJECT),
        Clue(name='Hammer', type=ClueType.WEAPON, subtype=ClueSubtype.OBJECT),

        # Color
        Clue(name='Bronze', type=ClueType.WEAPON, subtype=ClueSubtype.COLOR),
        Clue(name='Kupfer', type=ClueType.WEAPON, subtype=ClueSubtype.COLOR),
        Clue(name='Messing', type=ClueType.WEAPON, subtype=ClueSubtype.COLOR),
        Clue(name='Silber', type=ClueType.WEAPON, subtype=ClueSubtype.COLOR),

        # Condition
        Clue(name='Neu', type=ClueType.WEAPON, subtype=ClueSubtype.CONDITION),
        Clue(name='Gut', type=ClueType.WEAPON, subtype=ClueSubtype.CONDITION),
        Clue(name='Abgenutzt', type=ClueType.WEAPON, subtype=ClueSubtype.CONDITION)
    ]

    for weapon in weapons:
        weapon.save()


def create_crime_scenes():
    crime_scenes = [
        # Location
        Clue(name='See', type=ClueType.CRIME_SCENE, subtype=ClueSubtype.LOCATION),
        Clue(name='Höhle', type=ClueType.CRIME_SCENE, subtype=ClueSubtype.LOCATION),
        Clue(name='Schlachterei', type=ClueType.CRIME_SCENE, subtype=ClueSubtype.LOCATION),
        Clue(name='Friedhof', type=ClueType.CRIME_SCENE, subtype=ClueSubtype.LOCATION),
        Clue(name='Brücke', type=ClueType.CRIME_SCENE, subtype=ClueSubtype.LOCATION),
        Clue(name='Kanalisation', type=ClueType.CRIME_SCENE, subtype=ClueSubtype.LOCATION),
        Clue(name='Wald', type=ClueType.CRIME_SCENE, subtype=ClueSubtype.LOCATION),

        # Temperature
        Clue(name='Eisig', type=ClueType.CRIME_SCENE, subtype=ClueSubtype.TEMPERATURE),
        Clue(name='Kalt', type=ClueType.CRIME_SCENE, subtype=ClueSubtype.TEMPERATURE),
        Clue(name='Heiß', type=ClueType.CRIME_SCENE, subtype=ClueSubtype.TEMPERATURE),
        Clue(name='Schwül', type=ClueType.CRIME_SCENE, subtype=ClueSubtype.TEMPERATURE),

        # District
        Clue(name='West End', type=ClueType.CRIME_SCENE, subtype=ClueSubtype.DISTRICT),
        Clue(name='Westminster', type=ClueType.CRIME_SCENE, subtype=ClueSubtype.DISTRICT)
    ]

    for crime_scene in crime_scenes:
        crime_scene.save()


def create_offenders():
    offenders = [
        # Cloting
        Clue(name='Mantel', type=ClueType.OFFENDER, subtype=ClueSubtype.CLOTHING),
        Clue(name='Hut', type=ClueType.OFFENDER, subtype=ClueSubtype.CLOTHING),
        Clue(name='Umhang', type=ClueType.OFFENDER, subtype=ClueSubtype.CLOTHING),
        Clue(name='Anzug', type=ClueType.OFFENDER, subtype=ClueSubtype.CLOTHING),

        # Size
        Clue(name='Winzig', type=ClueType.OFFENDER, subtype=ClueSubtype.SIZE),
        Clue(name='Klein', type=ClueType.OFFENDER, subtype=ClueSubtype.SIZE),
        Clue(name='Durchschnitt', type=ClueType.OFFENDER, subtype=ClueSubtype.SIZE),
        Clue(name='Groß', type=ClueType.OFFENDER, subtype=ClueSubtype.SIZE),
        Clue(name='Riesig', type=ClueType.OFFENDER, subtype=ClueSubtype.SIZE),

        # Characteristic
        Clue(name='Narbe', type=ClueType.OFFENDER, subtype=ClueSubtype.CHARACTERISTIC),
        Clue(name='Perücke', type=ClueType.OFFENDER, subtype=ClueSubtype.CHARACTERISTIC),
        Clue(name='Tattoo', type=ClueType.OFFENDER, subtype=ClueSubtype.CHARACTERISTIC),
        Clue(name='Siegelring', type=ClueType.OFFENDER, subtype=ClueSubtype.CHARACTERISTIC),
        Clue(name='Leberfleck', type=ClueType.OFFENDER, subtype=ClueSubtype.CHARACTERISTIC)
    ]

    for offender in offenders:
        offender.save()


def create_time_of_crimes():
    time_of_crimes = [
        # Weekday
        Clue(name='Montag', type=ClueType.TIME_OF_CRIME, subtype=ClueSubtype.WEEKDAY),
        Clue(name='Dienstag', type=ClueType.TIME_OF_CRIME, subtype=ClueSubtype.WEEKDAY),
        Clue(name='Mittwoch', type=ClueType.TIME_OF_CRIME, subtype=ClueSubtype.WEEKDAY),
        Clue(name='Donnerstag', type=ClueType.TIME_OF_CRIME, subtype=ClueSubtype.WEEKDAY),
        Clue(name='Freitag', type=ClueType.TIME_OF_CRIME, subtype=ClueSubtype.WEEKDAY),
        Clue(name='Samstag', type=ClueType.TIME_OF_CRIME, subtype=ClueSubtype.WEEKDAY),
        Clue(name='Sonntag', type=ClueType.TIME_OF_CRIME, subtype=ClueSubtype.WEEKDAY),

        # Weekday
        Clue(name='am', type=ClueType.TIME_OF_CRIME, subtype=ClueSubtype.DAYTIME),
        Clue(name='pm', type=ClueType.TIME_OF_CRIME, subtype=ClueSubtype.DAYTIME),

        # Time
        Clue(name='2', type=ClueType.TIME_OF_CRIME, subtype=ClueSubtype.TIME),
        Clue(name='4', type=ClueType.TIME_OF_CRIME, subtype=ClueSubtype.TIME),
        Clue(name='6', type=ClueType.TIME_OF_CRIME, subtype=ClueSubtype.TIME),
        Clue(name='8', type=ClueType.TIME_OF_CRIME, subtype=ClueSubtype.TIME),
        Clue(name='10', type=ClueType.TIME_OF_CRIME, subtype=ClueSubtype.TIME),
        Clue(name='12', type=ClueType.TIME_OF_CRIME, subtype=ClueSubtype.TIME)
    ]

    for time_of_crime in time_of_crimes:
        time_of_crime.save()


def create_means_of_escape():
    means_of_escape = [
        # Model
        Clue(name='Automobil', type=ClueType.MEANS_OF_ESCAPE, subtype=ClueSubtype.MODEL),
        Clue(name='Kutsche', type=ClueType.MEANS_OF_ESCAPE, subtype=ClueSubtype.MODEL),
        Clue(name='Hochrad', type=ClueType.MEANS_OF_ESCAPE, subtype=ClueSubtype.MODEL),
        Clue(name='Pferd', type=ClueType.MEANS_OF_ESCAPE, subtype=ClueSubtype.MODEL),

        # Color
        Clue(name='Schwarz', type=ClueType.MEANS_OF_ESCAPE, subtype=ClueSubtype.COLOR),
        Clue(name='Weiß', type=ClueType.MEANS_OF_ESCAPE, subtype=ClueSubtype.COLOR),
        Clue(name='Kastanienbraun', type=ClueType.MEANS_OF_ESCAPE, subtype=ClueSubtype.COLOR),
        Clue(name='Rostrot', type=ClueType.MEANS_OF_ESCAPE, subtype=ClueSubtype.COLOR),

        # Escape Route
        Clue(name='Norden', type=ClueType.MEANS_OF_ESCAPE, subtype=ClueSubtype.ESCAPE_ROUTE),
        Clue(name='Osten', type=ClueType.MEANS_OF_ESCAPE, subtype=ClueSubtype.ESCAPE_ROUTE),
        Clue(name='Süden', type=ClueType.MEANS_OF_ESCAPE, subtype=ClueSubtype.ESCAPE_ROUTE),
        Clue(name='Westen', type=ClueType.MEANS_OF_ESCAPE, subtype=ClueSubtype.ESCAPE_ROUTE),
    ]

    for mean_of_escape in means_of_escape:
        mean_of_escape.save()


def create_clues():
    create_weapons()
    create_crime_scenes()
    create_offenders()
    create_time_of_crimes()
    create_means_of_escape()


def create_mime_pairs():
    # TODO: More mime pairs
    mime_pairs = [
        MimePair(correct_generic_term='Sommer', terms_to_be_mimed=array_2_string(['Schwimmen','Eis','Sonne']), fake_generic_terms=array_2_string(['Meer','Fisch','Wasser']))
    ]

    for mime_pair in mime_pairs:
        mime_pair.save()


def create_would_you_rather_pairs():
    wyr_pairs = [
        WouldYouRatherPair(a='Haut, die farblich Deine Gefühle widerspiegelt', b='Tattoos, die immer besagen, was Du die Nacht zuvor getan hast'),
        WouldYouRatherPair(a='Unsichtbar sein', b='Fliegen können'),
        WouldYouRatherPair(a='Wissen WANN Du stirbst', b='Wissen WIE Du stirbst'),
        WouldYouRatherPair(a='In den Weltraum reisen', b='In die Tiefe der Ozeane reisen'),
        WouldYouRatherPair(a='100 Jahre in die Vergangenheit reisen', b='100 Jahre in die Zukunft reisen'),
        WouldYouRatherPair(a='Reich sein', b='Unsterblich sein'),
        WouldYouRatherPair(a='Mit Tieren sprechen können', b='Alle Fremdsprachen sprechen können'),
        WouldYouRatherPair(a='Arm sein, aber Deinen Job lieben', b='Reich sein, aber Deinen Job hassen'),
        WouldYouRatherPair(a='Nicht lügen können', b='Alle Lügen glauben'),
        WouldYouRatherPair(a='Frei sein', b='Sicher sein')
    ]

    for wyr_pair in wyr_pairs:
        wyr_pair.save()


def db_init():
    # First delete data
    Clue.objects.all().delete()
    EventField.objects.all().delete()
    WouldYouRatherPair.objects.all().delete()
    MimePair.objects.all().delete()
    print("Deleted all db objects")

    # Then create data to be able to access them later
    create_event_fields()
    create_clues()
    create_would_you_rather_pairs()
    create_mime_pairs()
    print("Created all db objects")


def array_2_string(array):
    return ";".join(array)


def string_2_array(self, string):
    return string.split(";")