from .models import EventField, EventFieldType, Evidence, EvidenceSubtype, EvidenceType, MimePair, WouldYouRatherPair


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
        Evidence(name='Messer', type=EvidenceType.WEAPON, subtype=EvidenceSubtype.OBJECT),
        Evidence(name='Axt', type=EvidenceType.WEAPON, subtype=EvidenceSubtype.OBJECT),
        Evidence(name='Pistole', type=EvidenceType.WEAPON, subtype=EvidenceSubtype.OBJECT),
        Evidence(name='Hammer', type=EvidenceType.WEAPON, subtype=EvidenceSubtype.OBJECT),

        # Color
        Evidence(name='Bronze', type=EvidenceType.WEAPON, subtype=EvidenceSubtype.COLOR),
        Evidence(name='Kupfer', type=EvidenceType.WEAPON, subtype=EvidenceSubtype.COLOR),
        Evidence(name='Messing', type=EvidenceType.WEAPON, subtype=EvidenceSubtype.COLOR),
        Evidence(name='Silber', type=EvidenceType.WEAPON, subtype=EvidenceSubtype.COLOR),

        # Condition
        Evidence(name='Neu', type=EvidenceType.WEAPON, subtype=EvidenceSubtype.CONDITION),
        Evidence(name='Gut', type=EvidenceType.WEAPON, subtype=EvidenceSubtype.CONDITION),
        Evidence(name='Abgenutzt', type=EvidenceType.WEAPON, subtype=EvidenceSubtype.CONDITION)
    ]

    for weapon in weapons:
        weapon.save()


def create_crime_scenes():
    crime_scenes = [
        # Location
        Evidence(name='See', type=EvidenceType.CRIME_SCENE, subtype=EvidenceSubtype.LOCATION),
        Evidence(name='Höhle', type=EvidenceType.CRIME_SCENE, subtype=EvidenceSubtype.LOCATION),
        Evidence(name='Schlachterei', type=EvidenceType.CRIME_SCENE, subtype=EvidenceSubtype.LOCATION),
        Evidence(name='Friedhof', type=EvidenceType.CRIME_SCENE, subtype=EvidenceSubtype.LOCATION),
        Evidence(name='Brücke', type=EvidenceType.CRIME_SCENE, subtype=EvidenceSubtype.LOCATION),
        Evidence(name='Kanalisation', type=EvidenceType.CRIME_SCENE, subtype=EvidenceSubtype.LOCATION),
        Evidence(name='Wald', type=EvidenceType.CRIME_SCENE, subtype=EvidenceSubtype.LOCATION),

        # Temperature
        Evidence(name='Eisig', type=EvidenceType.CRIME_SCENE, subtype=EvidenceSubtype.TEMPERATURE),
        Evidence(name='Kalt', type=EvidenceType.CRIME_SCENE, subtype=EvidenceSubtype.TEMPERATURE),
        Evidence(name='Heiß', type=EvidenceType.CRIME_SCENE, subtype=EvidenceSubtype.TEMPERATURE),
        Evidence(name='Schwül', type=EvidenceType.CRIME_SCENE, subtype=EvidenceSubtype.TEMPERATURE),

        # District
        Evidence(name='West End', type=EvidenceType.CRIME_SCENE, subtype=EvidenceSubtype.DISTRICT),
        Evidence(name='Westminster', type=EvidenceType.CRIME_SCENE, subtype=EvidenceSubtype.DISTRICT)
    ]

    for crime_scene in crime_scenes:
        crime_scene.save()


def create_offenders():
    offenders = [
        # Cloting
        Evidence(name='Mantel', type=EvidenceType.OFFENDER, subtype=EvidenceSubtype.CLOTHING),
        Evidence(name='Hut', type=EvidenceType.OFFENDER, subtype=EvidenceSubtype.CLOTHING),
        Evidence(name='Umhang', type=EvidenceType.OFFENDER, subtype=EvidenceSubtype.CLOTHING),
        Evidence(name='Anzug', type=EvidenceType.OFFENDER, subtype=EvidenceSubtype.CLOTHING),

        # Size
        Evidence(name='Winzig', type=EvidenceType.OFFENDER, subtype=EvidenceSubtype.SIZE),
        Evidence(name='Klein', type=EvidenceType.OFFENDER, subtype=EvidenceSubtype.SIZE),
        Evidence(name='Durchschnitt', type=EvidenceType.OFFENDER, subtype=EvidenceSubtype.SIZE),
        Evidence(name='Groß', type=EvidenceType.OFFENDER, subtype=EvidenceSubtype.SIZE),
        Evidence(name='Riesig', type=EvidenceType.OFFENDER, subtype=EvidenceSubtype.SIZE),

        # Characteristic
        Evidence(name='Narbe', type=EvidenceType.OFFENDER, subtype=EvidenceSubtype.CHARACTERISTIC),
        Evidence(name='Perücke', type=EvidenceType.OFFENDER, subtype=EvidenceSubtype.CHARACTERISTIC),
        Evidence(name='Tattoo', type=EvidenceType.OFFENDER, subtype=EvidenceSubtype.CHARACTERISTIC),
        Evidence(name='Siegelring', type=EvidenceType.OFFENDER, subtype=EvidenceSubtype.CHARACTERISTIC),
        Evidence(name='Leberfleck', type=EvidenceType.OFFENDER, subtype=EvidenceSubtype.CHARACTERISTIC)
    ]

    for offender in offenders:
        offender.save()


def create_time_of_crimes():
    time_of_crimes = [
        # Weekday
        Evidence(name='Montag', type=EvidenceType.TIME_OF_CRIME, subtype=EvidenceSubtype.WEEKDAY),
        Evidence(name='Dienstag', type=EvidenceType.TIME_OF_CRIME, subtype=EvidenceSubtype.WEEKDAY),
        Evidence(name='Mittwoch', type=EvidenceType.TIME_OF_CRIME, subtype=EvidenceSubtype.WEEKDAY),
        Evidence(name='Donnerstag', type=EvidenceType.TIME_OF_CRIME, subtype=EvidenceSubtype.WEEKDAY),
        Evidence(name='Freitag', type=EvidenceType.TIME_OF_CRIME, subtype=EvidenceSubtype.WEEKDAY),
        Evidence(name='Samstag', type=EvidenceType.TIME_OF_CRIME, subtype=EvidenceSubtype.WEEKDAY),
        Evidence(name='Sonntag', type=EvidenceType.TIME_OF_CRIME, subtype=EvidenceSubtype.WEEKDAY),

        # Weekday
        Evidence(name='am', type=EvidenceType.TIME_OF_CRIME, subtype=EvidenceSubtype.DAYTIME),
        Evidence(name='pm', type=EvidenceType.TIME_OF_CRIME, subtype=EvidenceSubtype.DAYTIME),

        # Time
        Evidence(name='2', type=EvidenceType.TIME_OF_CRIME, subtype=EvidenceSubtype.TIME),
        Evidence(name='4', type=EvidenceType.TIME_OF_CRIME, subtype=EvidenceSubtype.TIME),
        Evidence(name='6', type=EvidenceType.TIME_OF_CRIME, subtype=EvidenceSubtype.TIME),
        Evidence(name='8', type=EvidenceType.TIME_OF_CRIME, subtype=EvidenceSubtype.TIME),
        Evidence(name='10', type=EvidenceType.TIME_OF_CRIME, subtype=EvidenceSubtype.TIME),
        Evidence(name='12', type=EvidenceType.TIME_OF_CRIME, subtype=EvidenceSubtype.TIME)
    ]

    for time_of_crime in time_of_crimes:
        time_of_crime.save()


def create_means_of_escape():
    means_of_escape = [
        # Model
        Evidence(name='Automobil', type=EvidenceType.MEANS_OF_ESCAPE, subtype=EvidenceSubtype.MODEL),
        Evidence(name='Kutsche', type=EvidenceType.MEANS_OF_ESCAPE, subtype=EvidenceSubtype.MODEL),
        Evidence(name='Hochrad', type=EvidenceType.MEANS_OF_ESCAPE, subtype=EvidenceSubtype.MODEL),
        Evidence(name='Pferd', type=EvidenceType.MEANS_OF_ESCAPE, subtype=EvidenceSubtype.MODEL),

        # Color
        Evidence(name='Schwarz', type=EvidenceType.MEANS_OF_ESCAPE, subtype=EvidenceSubtype.COLOR),
        Evidence(name='Weiß', type=EvidenceType.MEANS_OF_ESCAPE, subtype=EvidenceSubtype.COLOR),
        Evidence(name='Kastanienbraun', type=EvidenceType.MEANS_OF_ESCAPE, subtype=EvidenceSubtype.COLOR),
        Evidence(name='Rostrot', type=EvidenceType.MEANS_OF_ESCAPE, subtype=EvidenceSubtype.COLOR),

        # Escape Route
        Evidence(name='Norden', type=EvidenceType.MEANS_OF_ESCAPE, subtype=EvidenceSubtype.ESCAPE_ROUTE),
        Evidence(name='Osten', type=EvidenceType.MEANS_OF_ESCAPE, subtype=EvidenceSubtype.ESCAPE_ROUTE),
        Evidence(name='Süden', type=EvidenceType.MEANS_OF_ESCAPE, subtype=EvidenceSubtype.ESCAPE_ROUTE),
        Evidence(name='Westen', type=EvidenceType.MEANS_OF_ESCAPE, subtype=EvidenceSubtype.ESCAPE_ROUTE),
    ]

    for mean_of_escape in means_of_escape:
        mean_of_escape.save()


def create_evidences():
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
    Evidence.objects.all().delete()
    EventField.objects.all().delete()
    WouldYouRatherPair.objects.all().delete()
    MimePair.objects.all().delete()
    print("Deleted all db objects")

    # Then create data to be able to access them later
    create_event_fields()
    create_evidences()
    create_would_you_rather_pairs()
    create_mime_pairs()
    print("Created all db objects")


def array_2_string(array):
    return ";".join(array)


def string_2_array(self, string):
    return string.split(";")