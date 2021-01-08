from django.db import models


class ClueType(models.TextChoices):
    CRIME_SCENE = 'CS', 'Tatort'
    MEANS_OF_ESCAPE = 'ME', 'Fluchtmittel'
    OFFENDER = 'O', 'Täter'
    TIME_OF_CRIME = 'TC', 'Tatzeit'
    WEAPON = 'W', 'Waffen'


class ClueSubtype(models.TextChoices):
    CHARACTERISTIC = 'CC', 'Merkmal'
    CLOTHING = 'CG', 'Kleidung'
    COLOR = 'CR', 'Farbe'
    CONDITION = 'CN', 'Zustand'
    DAYTIME = 'DE', 'Tageszeit'
    DISTRICT = 'DT', 'Stadtviertel'
    ESCAPE_ROUTE = 'ER', 'Fluchtweg'
    LOCATION = 'L', 'Ort'
    MODEL = 'M', 'Modell'
    OBJECT = 'O', 'Gegenstand'
    SIZE = 'S', 'Größe'
    TEMPERATURE = 'TE', 'Temperatur'
    TIME = 'TI', 'Uhrzeit'
    WEEKDAY = 'W', 'Wochentag'


class Clue(models.Model):
    name = models.CharField(max_length=200, unique=True)
    type = models.CharField(max_length=2, choices=ClueType.choices, default=ClueType.WEAPON)
    subtype = models.CharField(max_length=2, choices=ClueSubtype.choices, default=ClueSubtype.OBJECT)


class EventFieldType(models.TextChoices):
    MINIGAME = 'M', 'Minigame'
    OCCASION = 'O', 'Occasion'


class EventField(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.CharField(max_length=200, default=None, blank=True, null=True)
    occasion_type = models.CharField(max_length=2, choices=EventFieldType.choices, default=EventFieldType.OCCASION)


class WouldYouRatherPair(models.Model):
    a = models.CharField(max_length=200, unique=True)
    b = models.CharField(max_length=200, unique=True)


class MimePair(models.Model):
    correct_generic_term = models.CharField(max_length=50)
    terms_to_be_mimed = models.CharField(max_length=200)
    fake_generic_terms = models.CharField(max_length=200)
