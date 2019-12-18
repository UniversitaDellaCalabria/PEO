import json

from django import forms
from django.contrib import admin
from django.urls import reverse
from django.utils import timezone
from django.utils.safestring import mark_safe

from django_form_builder.models import SavedFormContent
from django_form_builder.utils import get_allegati, get_as_dict
from unical_template.admin import ReadOnlyAdmin

from .admin_actions import (calcolo_punteggio_domanda,
                            download_report_graduatoria,
                            progressione_accettata,
                            verifica_allegati)
from .models import *


class ModuloDomandaBandoModelForm(forms.ModelForm):
    class Meta:
        model = ModuloDomandaBando
        fields = ('__all__')
        # widgets = {
            # 'modulo_compilato': forms.Textarea(attrs={'class':'vLargeTextField',
                                                      # 'style': 'disabled: true',
                                                     # }),
        # }

class ModuloDomandaBandoInLines(admin.StackedInline):
    model =  ModuloDomandaBando
    form = ModuloDomandaBandoModelForm
    readonly_fields = ('descrizione_indicatore',
                       # 'modulo_compilato',
                       'get_modulo_anteprima',
                       'get_modulo_grafica',
                       'punteggio_calcolato',
                       'download_pdf',
                       'created', 'modified')
    fields = ('descrizione_indicatore',
              'get_modulo_anteprima',
              'punteggio_calcolato',
              ('get_modulo_grafica', 'download_pdf',),
              ('created', 'modified'),
              ('disabilita','motivazione',))
    extra = 0
    classes = ['collapse',]

    def get_modulo_anteprima(self, obj):
        json_dict = json.loads(obj.modulo_compilato)
        data = get_as_dict(json_dict, allegati=False)
        allegati = get_allegati(obj)
        form = SavedFormContent.compiled_form_readonly(obj.compiled_form())

        table_tmpl = '<table margin-left: 15px;">{}</table>'
        allegati_html = ''

        for k,v in allegati:
            allegato_url = reverse('domande_peo:download_allegato',
                                   args=[obj.domanda_bando.bando.pk,
                                         obj.pk,
                                         k])
            allegati_html += '<tr><td>{}</td><td><a href="{}">{}</a><td></tr>'.format(k, allegato_url, v)


        value = form.as_table()
        v = table_tmpl.format(value)
        return  mark_safe(v+table_tmpl.format(allegati_html))
    get_modulo_anteprima.short_description = 'Modulo inserito'

    #def get_punteggio_reale(self, obj):
    #    domanda = obj.domanda_bando
    #    pos_eco = domanda.dipendente.livello.posizione_economica
    #    punteggio_raggiunto = domanda.calcolo_punteggio_max_descr_ind(obj.descrizione_indicatore,
    #                                                                  pos_eco)
    #    return punteggio_raggiunto
    #get_punteggio_reale.short_description = 'Punteggio Assegnabile'

    def download_pdf(self, obj):
        url = reverse('domande_peo:download_modulo_inserito_pdf',
                      args=(obj.domanda_bando.bando.pk,
                            obj.pk))
        a = ( "<button type='button' class='button' onClick=\""
              "window.open('{}','winname',"
              "'directories=no,titlebar=no,toolbar=no,location=no,"
              "status=no,menubar=no,scrollbars=no,resizable=no,"
              "width=890,height=600')"
              '"<span class="icon">Scarica PDF</span></button>').format(url)
        value = '{}'.format(a)
        return  mark_safe(value)
    download_pdf.short_description = 'Download PDF'

    def get_modulo_grafica(self, obj):
        url = reverse('domande_peo:vedi_modulo_inserito',
                      args=(obj.domanda_bando.bando.pk,
                            obj.pk))

        a = ( "<button type='button' class='button' onClick=\""
              "window.open('{}','winname',"
              "'directories=no,titlebar=no,toolbar=no,location=no,"
              "status=no,menubar=no,scrollbars=no,resizable=no,"
              "width=890,height=600')"
              '"<span class="icon">Vedi</span></button>').format(url)

        value = '{}'.format(a)
        return  mark_safe(value)
    get_modulo_grafica.short_description = 'Modulo inserito con grafica'


@admin.register(AbilitazioneBandoDipendente)
class AbilitazioneBandoDipendenteAdmin(admin.ModelAdmin):
    list_display = ('dipendente',
                    #'dipendente__matricola',
                    #'dipendente__nome',
                    #'dipendente__cognome',
                    'bando')
    list_filter = ('bando', 'dipendente__livello__nome',
                   'dipendente__livello__posizione_economica__nome')
    search_fields = ('dipendente__nome',
                     'dipendente__cognome',
                     'dipendente__matricola')

    autocomplete_fields = ['dipendente',]

    def has_add_permission(self, request):
        return False


class RettificaDomandaBandoInlineAdmin(admin.StackedInline):
    # list_display = ('domanda_bando__bando',
                    # 'domanda_bando__dipendente',
                    # 'created',)
    # list_filter = ('created',)
    # search_fields = ('domanda_bando__dipendente__utente__first_name',
                     # 'domanda_bando__dipendente__utente__last_name',
                     # 'domanda_bando__dipendente__matricola',
                     # 'numero_protocollo')
    model = RettificaDomandaBando
    extra = 0
    readonly_fields = ['created',
                       'numero_protocollo',
                       'data_protocollazione',
                       'data_chiusura',
                       'dump',]

    fieldsets = (
                (None, {'fields' : (
                                    ('created',),
                                    ('numero_protocollo', 'data_protocollazione'),
                                    ('data_chiusura',),
                                   )
                        }),
                ('Dump', {
                            'classes': ('collapse',),
                            'fields': (
                                        ('dump',),
                                       )
                        }

                ))


    # fields = (
                # ('created',),
                # ('numero_protocollo', 'data_protocollazione'),
                # ('dump',),
                # ('data_chiusura',),
             # )

    classes = ['collapse',]


@admin.register(DomandaBando)
class DomandaBandoAdmin(admin.ModelAdmin):
    list_display = ('get_dipendente_matricola',
                    'get_dipendente_nome',
                    'get_dipendente_cognome',
                    'bando',
                    'progressione_accettata',
                    'punteggio_calcolato',
                    'data_chiusura',
                    'numero_protocollo')
    list_filter = ('progressione_accettata',
                   'is_active',
                   'bando__nome',
                   'created',
                   'data_chiusura',
                   'dipendente__livello__posizione_economica__nome',
                   'dipendente__livello__nome',
                   )

    search_fields = ('dipendente__cognome', 'dipendente__matricola',)

    inlines = [RettificaDomandaBandoInlineAdmin,
               ModuloDomandaBandoInLines,]
    readonly_fields = ('dipendente', 'bando',
                       'created','punteggio_anzianita',
                       'numero_protocollo',
                       'data_protocollazione',
                       'get_modulo_grafica',
                       'download_pdf',
                       'get_dipendente_matricola',
                       'get_dipendente_nome',
                       'get_dipendente_cognome',)
    actions = [calcolo_punteggio_domanda, download_report_graduatoria,
               progressione_accettata, verifica_allegati]
    date_hierarchy = 'created'
    fields = (
                ('dipendente', 'bando'),
                'data_chiusura',
                ('numero_protocollo',), ('data_protocollazione',),
                ('livello', 'data_presa_servizio', 'data_ultima_progressione'),
                ('punteggio_anzianita','punteggio_anzianita_manuale',),
                'punteggio_calcolato',
                ('is_active', 'progressione_accettata',),
                ('commento_punteggio',),
                ('descrizione', 'created',),
                ('download_pdf', 'get_modulo_grafica',),
             )
    list_per_page = 600

    def get_dipendente_nome(self, obj):
        return obj.dipendente.nome
    get_dipendente_nome.short_description = 'Nome'
    get_dipendente_nome.admin_order_field = 'dipendente__nome'

    def get_dipendente_cognome(self, obj):
        return obj.dipendente.cognome
    get_dipendente_cognome.short_description = 'Cognome'
    get_dipendente_cognome.admin_order_field = 'dipendente__cognome'

    def get_dipendente_matricola(self, obj):
        return obj.dipendente.matricola
    get_dipendente_matricola.short_description = 'Matricola'
    get_dipendente_matricola.admin_order_field = 'dipendente__matricola'

    def punteggio_anzianita(self,obj):
        return obj.get_punteggio_anzianita()
    punteggio_anzianita.short_description = 'Punteggio assegnato all\'anzianità'

    def download_pdf(self, obj):
        url = reverse('domande_peo:download_domanda_pdf',
                      args=(obj.bando.pk,
                            obj.pk))
        a = ( "<button type='button' class='button' onClick=\""
              "window.open('{}','winname',"
              "'directories=no,titlebar=no,toolbar=no,location=no,"
              "status=no,menubar=no,scrollbars=no,resizable=no,"
              "width=890,height=600')"
              '"<span class="icon">Scarica PDF</span></button>').format(url)
        value = '{}'.format(a)
        return  mark_safe(value)
    download_pdf.short_description = 'Download PDF'

    def get_modulo_grafica(self, obj):
        url = reverse('domande_peo:riepilogo_domanda',
                      args=(obj.bando.pk, obj.pk))

        a = ( "<button type='button' class='button' onClick=\""
              "window.open('{}','winname',"
              "'directories=no,titlebar=no,toolbar=no,location=no,"
              "status=no,menubar=no,scrollbars=no,resizable=no,"
              "width=890,height=600')"
              '"<span class="icon">Vedi</span></button>').format(url)

        value = '{}'.format(a)
        return  mark_safe(value)
    get_modulo_grafica.short_description = 'Riepilogo Domanda con grafica'

    def save_model(self, request, obj, form, change):
        if obj.progressione_accettata:
            obj.dipendente.data_ultima_progressione_manuale = timezone.datetime(obj.bando.data_inizio.year,
                                                                                1, 1).date()
            obj.dipendente.save()
        super().save_model(request, obj, form, change)

    class Media:
        js = ('js/textarea-autosize_legacy.js',
              # 'js/jquery-ui/jquery-ui.min.js',
              'js/jquery-ui-django.js',
              'js/datepicker_onload.js')
        css = {'all': ('css/textarea-small.css',
                       'js/jquery-ui/jquery-ui.css',
                       'css/anteprima_modulo.css'),}



# @admin.register(ModuloDomandaBando)
# class ModuloDomandaBandoAdmin(admin.ModelAdmin):
    # list_display = ('dipendente', 'domanda_bando', 'progressione_accettata')
    # list_filter = ('progressione_accettata', 'is_active')
