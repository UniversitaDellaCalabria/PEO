from advanced_filters.admin import AdminAdvancedFiltersMixin

from django.contrib import admin
from django.contrib import messages
from django.conf import settings
from django.db.models import Q

from django.urls import reverse
from django.utils import timezone
from django.utils.safestring import mark_safe

from csa.models import _get_matricola, RUOLI

from .admin_actions import (abilita_idoneita_peo,
                            disabilita_idoneita_peo,
                            sincronizza_da_csa)
from .admin_inlines import *
from .admin_filters import *
from .models import *


@admin.register(PosizioneEconomica)
class PosizioneEconomicaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'punti_organico', 'descrizione')
    list_filter = ('nome',)
    inlines = [LivelloPosizioneEconomicaInline, ]

@admin.register(TitoloStudio)
class TitoloStudioAdmin(admin.ModelAdmin):
    list_display = ('nome', 'istituto', 'descrizione', 'isced_97_level',)
    search_fields = ('nome', 'istituto',)

# @admin.register(TipoInvalidita)
class TipoInvaliditaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'descrizione')
    list_filter = ('nome',)

# @admin.register(TipoProfiloProfessionale)
class TipoProfiloProfessionaleAdmin(admin.ModelAdmin):
    list_display = ('nome', 'descrizione')
    list_filter = ('nome',)

# @admin.register(LivelloPosizioneEconomica)
# class LivelloPosizioneEconomicaAdmin(admin.ModelAdmin):
    # list_display = ('get_categoria', 'posizione_economica', 'nome', )
    # list_filter = ('posizione_economica', 'nome',)
    # readonly_fields = ('get_descrizione',)
    #
    # def get_descrizione(self, obj):
        # admin_obj_url = reverse('admin:gestione_risorse_umane_posizioneeconomica_change', args=(obj.posizione_economica.pk,))
        # value = '{} <a href="{}"> [Modifica]</a>.'.format(obj.get_descrizione(),
                                                       # admin_obj_url,)
        # return mark_safe(value)
#
    # get_descrizione.short_description = 'Descrizione categoria Posizione Economica'

@admin.register(TipoContratto)
class TipoContrattoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'descrizione')
    list_filter = ('nome',)

@admin.register(Dipendente)
class DipendenteAdmin(AdminAdvancedFiltersMixin, admin.ModelAdmin):

    list_display = ('matricola', 'nome', 'cognome', 'livello',
                    # 'profilo',
                    'ruolo',
                    'afferenza_organizzativa',
                    # 'sede',
                    # 'get_in_servizio', 'idoneita_peo'
                    )

    # Creare customFilter get_in_servizio_adm
    list_filter = (
                   ('data_cessazione_contratto', DateRangeFilter),
                   ('data_presa_servizio', DateRangeFilter),
                   # ('pwdChangedTime', DateTimeRangeFilter),
                   CategoriaListFilter,
                   RuoloListFilter,
                   # InServizioListFilter,
                   # 'ruolo',
                   IdoneiPeoListFilter,
                   # AffOrgListFilter,
                   # SedeListFilter,
                   # MultipleCheckboxFilter,
                   )

    search_fields = ('matricola', 'nome',
                     'cognome')

    advanced_filter_fields = ('sede',
                              'afferenza_organizzativa__nome',
                              'ruolo',
                              'livello__nome',
                              'livello__posizione_economica__nome',
                              'profilo__nome',
                              'data_presa_servizio',
                              'data_cessazione_contratto')

    readonly_fields = ('livello', 'ruolo',
                       'sede',
                       'afferenza_organizzativa',
                       'data_presa_servizio',
                       'data_cessazione_contratto',
                       'profilo',
                       'get_progressione',
                       'get_data_presa_servizio_csa',
                       'get_sede_csa',
                       'get_ds_inquadramento_csa',
                       'get_inquadramento_csa',
                       'get_profilo_csa',
                       'get_data_cessazione_contratto_csa',
                       'data_ultima_sincronizzazione',
                       'link_dati_csa')

    fieldsets = (
        (None, { 'fields' : ('data_ultima_sincronizzazione',
                            ('matricola', 'utente',),
                            ('livello', 'ruolo', ),
                             # 'profilo', 'invalidita'),
                            ('invalidita',),
                            'profilo',
                            ('afferenza_organizzativa', 'sede',),
                             'motivo_cessazione_contratto',
                            ('carta_identita_front', 'carta_identita_retro'),
                             'descrizione',
                             'get_progressione',
                             'disattivato'
                           # 'ultima_progressione',
                           # 'is_active', 'descrizione',
                           ),}),
        ('Date PresaServizio, UltimaProgressione e CessazioneContratto', {
            'fields': (
                        ('data_presa_servizio_manuale',
                         'data_ultima_progressione_manuale',
                         'data_cessazione_contratto_manuale',),
                        ('data_presa_servizio', 'data_cessazione_contratto',),
                      ),
        }),
        ('Dati CSA', {
            'classes': ('collapse',),
            'fields': (('get_profilo_csa',
                        'get_inquadramento_csa',
                        'get_ds_inquadramento_csa',),
                        'get_sede_csa',
                       #('get_data_presa_servizio_csa',
                       # 'get_data_cessazione_contratto_csa'),
                        'link_dati_csa'),
                      }
        )
    )
    list_per_page = 300
    autocomplete_fields = ['utente',]
    actions = [abilita_idoneita_peo, disabilita_idoneita_peo]
    if settings.CSA_MODE == 'native':
        actions.append(sincronizza_da_csa)

    class Media:
        js = ('js/textarea-autosize.js',)
        css = {'all': ('css/textarea-small.css',),}

    def get_inquadramento_csa(self, obj):
        c =  obj.get_inquadramento_csa()
        if c: return c[0]
    get_inquadramento_csa.short_description = 'Inquadramento (CSA)'

    def get_ds_inquadramento_csa(self, obj):
        c =  obj.get_inquadramento_csa()
        if c: return c[1]
    get_ds_inquadramento_csa.short_description = 'Descrizione Inquadramento (CSA)'

    def get_profilo_csa(self, obj):
        c =  obj.get_profilo_csa()
        return c
    get_profilo_csa.short_description = 'Profilo (CSA)'

    def get_data_cessazione_contratto_csa(self, obj):
        return obj.get_data_cessazione_servizio_csa().strftime(settings.STRFTIME_DATE_FORMAT)
    get_data_cessazione_contratto_csa.short_description = 'Data cessazione contratto (CSA)'

    def get_sede_csa(self, obj):
        return obj.get_sede_csa()
    get_sede_csa.short_description = 'Afferenza Organizzativa (CSA)'

    def get_data_presa_servizio_csa(self, obj):
        return obj.get_data_presa_servizio_csa().strftime(settings.STRFTIME_DATE_FORMAT)
    get_data_presa_servizio_csa.short_description = 'data presa servizio (CSA)'

    # def get_in_servizio(self, obj):
        # return obj.get_in_servizio()
    # get_in_servizio.boolean = True
    # get_in_servizio.short_description = 'in servizio'

    def idoneita_peo(self, obj):
        return obj.idoneita_peo()
    idoneita_peo.boolean = True
    idoneita_peo.short_description = 'Idoneità PEO'

    def link_dati_csa(self, obj):
        admin_obj_url = reverse('admin:csa_v_anagrafica_change', args=(_get_matricola(obj.matricola),))
        value = '<a href="{}">Cosulta Incarichi e Carriera CSA</a>.'.format(admin_obj_url)
        return mark_safe(value)

    def get_progressione(self, obj):
        return obj.get_data_progressione()
        # admin_obj_url = reverse('admin:domande_peo_domandabando_change', args=(obj.get_domanda_progressione().pk,))
        # value = '{} - <a href="{}">Domanda: {}</a>.'.format( obj.get_data_progressione().strftime(settings.STRFTIME_DATE_FORMAT),
                                                             # admin_obj_url,
                                                             # obj.get_domanda_progressione() )
        # return mark_safe(value)
    get_progressione.short_description = 'Ultima progressione'
