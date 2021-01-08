from django.contrib import admin
from .models import EventField, Evidence, MimePair, WouldYouRatherPair

#Register your models here.
admin.site.register(EventField)
admin.site.register(Evidence)
admin.site.register(MimePair)
admin.site.register(WouldYouRatherPair)
