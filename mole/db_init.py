from .models import EventField, EventFieldType, Evidence, EvidenceSubtype, EvidenceType, MimePair, WouldYouRatherPair

def create_event_fields():
    event_fields = [
        EventField(name='Hinweis suchen', description='Du hast die Möglichkeit einen Hinweis zu finden. Hierfür musst Du versuchen eine sechs zu würfeln. Du hast nur einen Versuch! Gib unten an, ob du es geschafft hast.', occasion_type=EventFieldType.OCCASION),
        EventField(name='X Felder vor', description='Du hast die Möglichkeit dein Team voranzubringen. Du darfst einmal würfeln. Gib unten die gewürfelte Zahl an.', occasion_type=EventFieldType.OCCASION),
        EventField(name='Würfeln erleichtern', description='Mit Deiner Hilfe wurde das Würfeln für die nachfolgende Person erleichtert.', occasion_type=EventFieldType.OCCASION),
        EventField(name='Aussetzen von gewählten Personen', description='Du darfst unten zwei Personen auswählen, die eine Runde aussetzen müssen.', occasion_type=EventFieldType.OCCASION),
        EventField(name='X Felder zurück', description='Du musst einmal würfeln. Dein Team muss die gewürfelte Zahl an Feldern zurückgehen. Gib unten die gewürfelte Zahl an.', occasion_type=EventFieldType.OCCASION),
        EventField(name='Würfeln erschweren', description='', occasion_type=EventFieldType.OCCASION),

        EventField(name='The Trust Game', description='Wer ist nur der Maulwurf? Du bist misstrauisch und unterziehst Dein Teammitglied einem Vertrauenstest: dem Trust Game.\nIhr bekommt nun zwei Szenarien vorgestellt, und müsst angeben, was Ihr selbst eher tun würdet, und was Ihr vermutet, was der andere eher tun würde. Korrekte Vermutungen geben Punkte fürs Team. Dein Spielpartner ist', occasion_type=EventFieldType.MINIGAME),
        EventField(name='The Silence Game', description='Was war das für ein Geräusch? Könnte das Euer Verfolger gewesen sein?\nIhr dürft kein Riskoeingehen, und müsst Euch sofort alle leise verhalten! Trotzdem müsst Ihr im Team weiter kommunizieren.\nDein Team wird dir gleich für 30 Sekunden verschiedene Begriffe mittels Pantomime erklären. Du musst erraten, welcher Oberbegriff gemeint ist, der die einzelnen Begriffe verbindet.', occasion_type=EventFieldType.MINIGAME),
        EventField(name='The Lock Picking Game',description='Euer Verfolger ist Euch knapp auf den Fersen, aber dieser Weg ist mit einem Schloss versperrt!\nNur gemeinsam könnt ihr es knacken - jeder Spieler ist für einen Stift in der Mechanik verantwortlich, sodass Du die Haarnadel nutzen kannst, um das Schloss zu knacken.\nIhr habt eine Minute - wenn Ihr es nicht schafft, könnt Ihr diesen Weg nicht nutzen ...', occasion_type=EventFieldType.MINIGAME)

    ]

    for field in event_fields:
        field.save()


def create_weapons():
    weapons = [
        # Object
        Evidence(name='Messer', evidence_type=EvidenceType.WEAPON, evidence_subtype=EvidenceSubtype.OBJECT),
        Evidence(name='Axt', evidence_type=EvidenceType.WEAPON, evidence_subtype=EvidenceSubtype.OBJECT),
        Evidence(name='Pistole', evidence_type=EvidenceType.WEAPON, evidence_subtype=EvidenceSubtype.OBJECT),
        Evidence(name='Hammer', evidence_type=EvidenceType.WEAPON, evidence_subtype=EvidenceSubtype.OBJECT),

        # Color
        Evidence(name='Bronze', evidence_type=EvidenceType.WEAPON, evidence_subtype=EvidenceSubtype.COLOR),
        Evidence(name='Kupfer', evidence_type=EvidenceType.WEAPON, evidence_subtype=EvidenceSubtype.COLOR),
        Evidence(name='Messing', evidence_type=EvidenceType.WEAPON, evidence_subtype=EvidenceSubtype.COLOR),
        Evidence(name='Silber', evidence_type=EvidenceType.WEAPON, evidence_subtype=EvidenceSubtype.COLOR),

        # Condition
        Evidence(name='Neu', evidence_type=EvidenceType.WEAPON, evidence_subtype=EvidenceSubtype.CONDITION),
        Evidence(name='Gut', evidence_type=EvidenceType.WEAPON, evidence_subtype=EvidenceSubtype.CONDITION),
        Evidence(name='Abgenutzt', evidence_type=EvidenceType.WEAPON, evidence_subtype=EvidenceSubtype.CONDITION)
    ]

    for weapon in weapons:
        weapon.save()


def create_crime_scenes():
    crime_scenes = [
        # Location
        Evidence(name='See', evidence_type=EvidenceType.CRIME_SCENE, evidence_subtype=EvidenceSubtype.LOCATION),
        Evidence(name='Höhle', evidence_type=EvidenceType.CRIME_SCENE, evidence_subtype=EvidenceSubtype.LOCATION),
        Evidence(name='Schlachterei', evidence_type=EvidenceType.CRIME_SCENE, evidence_subtype=EvidenceSubtype.LOCATION),
        Evidence(name='Friedhof', evidence_type=EvidenceType.CRIME_SCENE, evidence_subtype=EvidenceSubtype.LOCATION),
        Evidence(name='Brücke', evidence_type=EvidenceType.CRIME_SCENE, evidence_subtype=EvidenceSubtype.LOCATION),
        Evidence(name='Kanalisation', evidence_type=EvidenceType.CRIME_SCENE, evidence_subtype=EvidenceSubtype.LOCATION),
        Evidence(name='Wald', evidence_type=EvidenceType.CRIME_SCENE, evidence_subtype=EvidenceSubtype.LOCATION),

        # Temperature
        Evidence(name='Eisig', evidence_type=EvidenceType.CRIME_SCENE, evidence_subtype=EvidenceSubtype.TEMPERATURE),
        Evidence(name='Kalt', evidence_type=EvidenceType.CRIME_SCENE, evidence_subtype=EvidenceSubtype.TEMPERATURE),
        Evidence(name='Heiß', evidence_type=EvidenceType.CRIME_SCENE, evidence_subtype=EvidenceSubtype.TEMPERATURE),
        Evidence(name='Schwül', evidence_type=EvidenceType.CRIME_SCENE, evidence_subtype=EvidenceSubtype.TEMPERATURE),

        # District
        Evidence(name='West End', evidence_type=EvidenceType.CRIME_SCENE, evidence_subtype=EvidenceSubtype.DISTRICT),
        Evidence(name='Westminster', evidence_type=EvidenceType.CRIME_SCENE, evidence_subtype=EvidenceSubtype.DISTRICT)
    ]

    for crime_scene in crime_scenes:
        crime_scene.save()


def create_offenders():
    offenders = [
        # Cloting
        Evidence(name='Mantel', evidence_type=EvidenceType.OFFENDER, evidence_subtype=EvidenceSubtype.CLOTHING),
        Evidence(name='Hut', evidence_type=EvidenceType.OFFENDER, evidence_subtype=EvidenceSubtype.CLOTHING),
        Evidence(name='Umhang', evidence_type=EvidenceType.OFFENDER, evidence_subtype=EvidenceSubtype.CLOTHING),
        Evidence(name='Anzug', evidence_type=EvidenceType.OFFENDER, evidence_subtype=EvidenceSubtype.CLOTHING),

        # Size
        Evidence(name='Winzig', evidence_type=EvidenceType.OFFENDER, evidence_subtype=EvidenceSubtype.SIZE),
        Evidence(name='Klein', evidence_type=EvidenceType.OFFENDER, evidence_subtype=EvidenceSubtype.SIZE),
        Evidence(name='Durchschnitt', evidence_type=EvidenceType.OFFENDER, evidence_subtype=EvidenceSubtype.SIZE),
        Evidence(name='Groß', evidence_type=EvidenceType.OFFENDER, evidence_subtype=EvidenceSubtype.SIZE),
        Evidence(name='Riesig', evidence_type=EvidenceType.OFFENDER, evidence_subtype=EvidenceSubtype.SIZE),

        # Characteristic
        Evidence(name='Narbe', evidence_type=EvidenceType.OFFENDER, evidence_subtype=EvidenceSubtype.CHARACTERISTIC),
        Evidence(name='Perücke', evidence_type=EvidenceType.OFFENDER, evidence_subtype=EvidenceSubtype.CHARACTERISTIC),
        Evidence(name='Tattoo', evidence_type=EvidenceType.OFFENDER, evidence_subtype=EvidenceSubtype.CHARACTERISTIC),
        Evidence(name='Siegelring', evidence_type=EvidenceType.OFFENDER, evidence_subtype=EvidenceSubtype.CHARACTERISTIC),
        Evidence(name='Leberfleck', evidence_type=EvidenceType.OFFENDER, evidence_subtype=EvidenceSubtype.CHARACTERISTIC)
    ]

    for offender in offenders:
        offender.save()


def create_time_of_crimes():
    time_of_crimes = [
        # Weekday
        Evidence(name='Montag', evidence_type=EvidenceType.TIME_OF_CRIME, evidence_subtype=EvidenceSubtype.WEEKDAY),
        Evidence(name='Dienstag', evidence_type=EvidenceType.TIME_OF_CRIME, evidence_subtype=EvidenceSubtype.WEEKDAY),
        Evidence(name='Mittwoch', evidence_type=EvidenceType.TIME_OF_CRIME, evidence_subtype=EvidenceSubtype.WEEKDAY),
        Evidence(name='Donnerstag', evidence_type=EvidenceType.TIME_OF_CRIME, evidence_subtype=EvidenceSubtype.WEEKDAY),
        Evidence(name='Freitag', evidence_type=EvidenceType.TIME_OF_CRIME, evidence_subtype=EvidenceSubtype.WEEKDAY),
        Evidence(name='Samstag', evidence_type=EvidenceType.TIME_OF_CRIME, evidence_subtype=EvidenceSubtype.WEEKDAY),
        Evidence(name='Sonntag', evidence_type=EvidenceType.TIME_OF_CRIME, evidence_subtype=EvidenceSubtype.WEEKDAY),

        # Weekday
        Evidence(name='am', evidence_type=EvidenceType.TIME_OF_CRIME, evidence_subtype=EvidenceSubtype.DAYTIME),
        Evidence(name='pm', evidence_type=EvidenceType.TIME_OF_CRIME, evidence_subtype=EvidenceSubtype.DAYTIME),

        # Time
        Evidence(name='2', evidence_type=EvidenceType.TIME_OF_CRIME, evidence_subtype=EvidenceSubtype.TIME),
        Evidence(name='4', evidence_type=EvidenceType.TIME_OF_CRIME, evidence_subtype=EvidenceSubtype.TIME),
        Evidence(name='6', evidence_type=EvidenceType.TIME_OF_CRIME, evidence_subtype=EvidenceSubtype.TIME),
        Evidence(name='8', evidence_type=EvidenceType.TIME_OF_CRIME, evidence_subtype=EvidenceSubtype.TIME),
        Evidence(name='10', evidence_type=EvidenceType.TIME_OF_CRIME, evidence_subtype=EvidenceSubtype.TIME),
        Evidence(name='12', evidence_type=EvidenceType.TIME_OF_CRIME, evidence_subtype=EvidenceSubtype.TIME)
    ]

    for time_of_crime in time_of_crimes:
        time_of_crime.save()


def create_means_of_escape():
    means_of_escape = [
        # Model
        Evidence(name='Automobil', evidence_type=EvidenceType.MEANS_OF_ESCAPE, evidence_subtype=EvidenceSubtype.MODEL),
        Evidence(name='Kutsche', evidence_type=EvidenceType.MEANS_OF_ESCAPE, evidence_subtype=EvidenceSubtype.MODEL),
        Evidence(name='Hochrad', evidence_type=EvidenceType.MEANS_OF_ESCAPE, evidence_subtype=EvidenceSubtype.MODEL),
        Evidence(name='Pferd', evidence_type=EvidenceType.MEANS_OF_ESCAPE, evidence_subtype=EvidenceSubtype.MODEL),

        # Color
        Evidence(name='Schwarz', evidence_type=EvidenceType.MEANS_OF_ESCAPE, evidence_subtype=EvidenceSubtype.COLOR),
        Evidence(name='Weiß', evidence_type=EvidenceType.MEANS_OF_ESCAPE, evidence_subtype=EvidenceSubtype.COLOR),
        Evidence(name='Kastanienbraun', evidence_type=EvidenceType.MEANS_OF_ESCAPE, evidence_subtype=EvidenceSubtype.COLOR),
        Evidence(name='Rostrot', evidence_type=EvidenceType.MEANS_OF_ESCAPE, evidence_subtype=EvidenceSubtype.COLOR),

        # Escape Route
        Evidence(name='Norden', evidence_type=EvidenceType.MEANS_OF_ESCAPE, evidence_subtype=EvidenceSubtype.ESCAPE_ROUTE),
        Evidence(name='Osten', evidence_type=EvidenceType.MEANS_OF_ESCAPE, evidence_subtype=EvidenceSubtype.ESCAPE_ROUTE),
        Evidence(name='Süden', evidence_type=EvidenceType.MEANS_OF_ESCAPE, evidence_subtype=EvidenceSubtype.ESCAPE_ROUTE),
        Evidence(name='Westen', evidence_type=EvidenceType.MEANS_OF_ESCAPE, evidence_subtype=EvidenceSubtype.ESCAPE_ROUTE),
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
    create_event_fields()
    create_evidences()
    create_would_you_rather_pairs()
    create_mime_pairs()


def array_2_string(array):
    return ";".join(array)


def string_2_array(self, string):
    return string.split(";")
