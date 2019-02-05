from django.contrib import admin
from .models import *
    
class LivelloPosizioneEconomicaInline(admin.TabularInline):
	 model = LivelloPosizioneEconomica
	 extra = 0
