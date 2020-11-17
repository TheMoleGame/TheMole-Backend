from django.db import models


class EvidenceType(models.TextChoices):
    CRIME_SCENE = 'CS', 'Tatort'
    MEANS_OF_ESCAPE = 'ME', 'Fluchtmittel'
    OFFENDER = 'O', 'Täter'
    TIME_OF_CRIME = 'TC', 'Tatzeit'
    WEAPON = 'W', 'Waffen'


class EvidenceSubtype(models.TextChoices):
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


class Evidence(models.Model):
    name = models.CharField(max_length=200)
    evidence_type = models.CharField(max_length=2, choices=EvidenceType.choices, default=EvidenceType.WEAPON)
    evidence_subtype = models.CharField(max_length=2, choices=EvidenceSubtype.choices, default=EvidenceSubtype.OBJECT)


class EventFieldType(models.TextChoices):
    MINIGAME = 'M', 'Minigame'
    OCCASION = 'O', 'Occasion'


class EventField(models.Model):
    name = models.CharField(max_length=50)
    description = models.CharField(max_length=200)
    occasion_type = models.CharField(max_length=2, choices=EventFieldType.choices, default=EventFieldType.OCCASION)


class WouldYouRatherPair(models.Model):
    a = models.CharField(max_length=200)
    b = models.CharField(max_length=200)


class MimePair(models.Model):
    correct_generic_term = models.CharField(max_length=50)
    terms_to_be_mimed = models.CharField(max_length=200)
    fake_generic_terms = models.CharField(max_length=200)
