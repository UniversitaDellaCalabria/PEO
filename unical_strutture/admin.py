from django.contrib import admin

from .models import *
from .admin_inlines import *

@admin.register(FunzioneLocazioneStruttura)
class FunzioneLocazioneStruttura(admin.ModelAdmin):
    list_display = ('nome', 'descrizione')

    class Media:
        js = ('js/textarea-autosize.js',)
        css = {'all': ('css/textarea-small.css',),}


@admin.register(TipoStruttura)
class TipoStrutturaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'descrizione')

    class Media:
        js = ('js/textarea-autosize.js',)
        css = {'all': ('css/textarea-small.css',),}


@admin.register(Struttura)
class StrutturaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'tipo', 'sede','is_active')
    list_filter = ('tipo', 'is_active')
    inlines = [LocazioneStrutturaInline,]
    
    class Media:
        js = ('js/textarea-autosize.js',)
        css = {'all': ('css/textarea-small.css',),}


@admin.register(TipoDotazione)
class TipoDotazioneAdmin(admin.ModelAdmin):
    list_display = ('nome', 'descrizione')

    class Media:
        js = ('js/textarea-autosize.js',)
        css = {'all': ('css/textarea-small.css',),}

@admin.register(Locazione)
class LocazioneAdmin(admin.ModelAdmin):
    list_display = ('nome', 'indirizzo', 'descrizione_breve',)
    # list_filter = ('')

    class Media:
        js = ('js/textarea-autosize.js',)
        css = {'all': ('css/textarea-small.css',),}

# @admin.register(LocazioneStruttura)
# class LocazioneStrutturaAdmin(admin.ModelAdmin):
    # list_display = ('struttura', 'descrizione_breve', 'locazione', 'telefono', 'is_active')
    # list_filter = ('dotazione', 'funzione', 'is_active')
# 
    # class Media:
        # js = ('js/textarea-autosize.js',)
        # css = {'all': ('css/textarea-small.css',),}
