import nested_admin

from django.contrib import admin

from .admin_inlines import *
from .admin_nested_inlines import *
from .models import *
from .admin_actions import duplica_bando, scarica_template_bando


@admin.register(Bando)
#class BandoAdmin(admin.ModelAdmin):
class BandoAdmin(nested_admin.NestedModelAdmin):
    prepopulated_fields = {"slug": ("nome",)}
    actions = [duplica_bando,
               scarica_template_bando]
    list_display = ('nome',
                    'data_inizio',
                    'data_fine_presentazione_domande',
                    'data_fine',
                    'ultima_progressione',
                    # 'descrizione',
                    'collaudo',
                    'pubblicato',
                    'redazione',
                    'created',)
    list_filter = ('redazione', 'collaudo', 'pubblicato')
    list_editable = ('collaudo', 'redazione', 'pubblicato')
    search_fields = ('nome',)
    inlines = [ClausoleBandoNestedInline,
               #IndicatorePonderatoInline,
               Punteggio_TitoloStudioNestedInline,
               CategorieDisabilitate_TitoloStudioNestedInline,
               Punteggio_Anzianita_ServizioNestedInline]

    date_hierarchy = 'data_inizio'

    fieldsets = (
             (None, {
                        # 'classes': ('collapse',),
                        'fields' : (
                                      ('nome', 'slug',),
                                      ('descrizione',),
                                      ('bando_url',),
                                      ('accettazione_clausole_text'),
                                      ('redazione', 'collaudo', 'pubblicato'),
                                      ('email_avvenuto_completamento', 'pubblica_punteggio'),
                                    )
                       },
             ),
             ('Date, termini, scadenze e soglie temporali generali',
                                {
                                'fields' : (
                                            ('data_inizio', ),
                                            'data_fine',
                                            ('data_fine_presentazione_domande',),
                                           )
                                },
             ),
             ('Date, termini, scadenze e soglie temporali specifiche',
                                {
                                'fields' : (
                                            ('data_validita_titoli_fine'),
                                            ('ultima_progressione', 'anni_servizio_minimi'),
                                           )
                                },
             ),
             ('Modalità valutazione punteggio',
                                {
                                'fields' : (
                                             ('agevolazione_soglia_anni', 'agevolazione_fatmol'),
                                              ( 'priorita_titoli_studio',),
                                            )
                                },
              ),

              ('GESTIONE PROTOCOLLO INFORMATICO', {
                                'classes': ('collapse',),
                                'fields' : (
                                            ('protocollo_cod_titolario',
                                             'protocollo_fascicolo_numero'),
                                            ('protocollo_required',),
                                            ('protocollo_template'),
                                            )
                             },
              ),
        )

    class Media:
        js = ('js/textarea-autosize_legacy.js',)
        css = {'all': ('css/textarea-small.css',),}

@admin.register(IndicatorePonderato)
class IndicatorePonderatoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'id_code', 'bando')
    inlines = [ PunteggioMaxIndicatorePonderatoPosizioneEconomicaInline,]
    list_filter = ('bando__nome', 'id_code',)
    #inlines = [IndicatoreTitoloInline]
    autocomplete_fields = ['bando',]
    date_hierarchy = 'created'
    search_fields = ('nome', 'bando__nome',)
    class Media:
        js = ('js/textarea-autosize_legacy.js',)


@admin.register(DescrizioneIndicatore)
class DescrizioneIndicatoreAdmin(DescrizioneIndicatoreAdminAbstract, nested_admin.NestedModelAdmin):
    list_display = ('nome', 'id_code', 'indicatore_ponderato') #, 'note')
    list_filter = ('indicatore_ponderato__bando__nome',
                   'id_code',
                   'non_cancellabile',
                   'is_required')
    inlines = [Punteggio_DescrizioneIndicatoreNestedInline,
               Punteggio_DescrizioneIndicatore_TimeDeltaNestedInline,
               PunteggioMax_DescrizioneIndicatore_PosEconomicaNestedInline,
               ModuloInserimentoCampiNestedInline,
               CategorieDisabilitate_DescrizioneIndicatoreNestedInline,
               RuoliDisabilitati_DescrizioneIndicatoreNestedInline]

    readonly_fields = ('get_anteprima_modulo_inserimento',)
    search_fields = ('nome', 'indicatore_ponderato__bando__nome',)
    fields = ('indicatore_ponderato',
              ('nome', 'id_code'),
              ('note'),
              ('calcolo_punteggio_automatico'),
              ('non_cancellabile'),
              ('is_required'),
              ('limite_inserimenti','numero_inserimenti'),
              ('get_anteprima_modulo_inserimento')
              )

    autocomplete_fields = ['indicatore_ponderato',]
    date_hierarchy = 'indicatore_ponderato__bando__data_inizio'

    class Media:
        js = ('js/textarea-autosize_legacy.js',)


# @admin.register(ClausoleBando)
# class ClausoleBandoAdmin(admin.ModelAdmin):
    # list_display = ('titolo', 'bando') #, 'note')
    #list_filter = ('indicatore_ponderato__bando__nome', 'id_code',)
    #inlines = [ Punteggio_DescrizioneIndicatoreInline,
    #            Punteggio_DescrizioneIndicatore_TimeDeltaInline,
    #            PunteggioMax_DescrizioneIndicatore_PosEconomicaInline,
    #            ModuloInserimentoCampiInline,
    #           ]


    # class Media:
        # js = ('js/textarea-autosize_legacy.js',)


# i seguenti li lasciamo in caso di attivazione postuma
# di fatto non servono perchè gestiti inline


# @admin.register(PunteggioTitoloStudio)
# class PunteggioTitoloStudioAdmin(admin.ModelAdmin):
    # list_display = ('punteggio',)
    # list_filter = ('punteggio',)


#@admin.register(CategorieDisabilitatePunteggioTitoloStudio)
# class CategorieDisabilitatePunteggioTitoloStudioAdmin(admin.ModelAdmin):
    # pass


# @admin.register(PunteggioAnzianitaDiServizio)
# class PunteggioAnzianitaDiServizioAdmin(admin.ModelAdmin):
   # list_display = ('punteggio_max', 'punteggio')


@admin.register(SubDescrizioneIndicatore)
class SubDescrizioneIndicatoreAdmin(nested_admin.NestedModelAdmin):
    list_display = ('nome', 'id_code', 'descrizione_indicatore') #, 'note')
    list_filter = ('descrizione_indicatore__indicatore_ponderato__bando__nome',
                   'id_code')
    inlines = [ Punteggio_SubDescrizioneIndicatoreNestedInline,
                Punteggio_SubDescrizioneIndicatore_TimeDeltaNestedInline,
                PunteggioMax_SubDescrizioneIndicatore_PosEconomicaNestedInline,
               ]

    search_fields = ('nome',)
    fields = ('descrizione_indicatore',
              ('nome', 'id_code'),
              ('note'),
              )
    autocomplete_fields = ['descrizione_indicatore',]
    # autocomplete_fields = ['indicatore_ponderato',]
    date_hierarchy = 'descrizione_indicatore__indicatore_ponderato__bando__data_inizio'

    class Media:
        js = ('js/textarea-autosize_legacy.js',)
