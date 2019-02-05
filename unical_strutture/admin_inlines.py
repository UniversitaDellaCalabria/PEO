from django import forms
from django.contrib import admin

from .models import *

class LocazioneStrutturaInline(admin.TabularInline):
	 model = LocazioneStruttura
	 extra = 0
