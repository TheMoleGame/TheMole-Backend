from django.contrib import admin
from .models import EventField, Clue, MimePair, WouldYouRatherPair

#Register your models here.
admin.site.register(EventField)
admin.site.register(Clue)
admin.site.register(MimePair)
admin.site.register(WouldYouRatherPair)
