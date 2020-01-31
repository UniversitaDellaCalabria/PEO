import os

from django.apps import apps
from django.contrib import messages
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponse
from django.utils import timezone

from .models import *
from .utils import export_graduatoria_csv


def _calcolo_punteggio_domanda(modeladmin,
                               request,
                               queryset,
                               save=True,
                               ignora_disabilitati=False,
                               show_warnings=False):
    num = 0
    failed = 0
    msg_err = 'Sono incorsi errori nel calcolare {}: {}'
    msg_ok = '{}, punteggio: {}'
    if show_warnings:
        msg_ok = '{}, punteggio: {} (senza tener conto delle soglie: {} / decurtato: {})'
    for i in queryset:
        try:
            results = i.calcolo_punteggio_domanda(save=save,
                                                  ignora_disabilitati=ignora_disabilitati)
            num += 1
            if show_warnings:
                msg = msg_ok.format(i, results[1], results[0],
                                    float("{:.2f}".format(results[0]-results[1])))
            else:
                msg = msg_ok.format(i, results[1])
            messages.add_message(request, messages.INFO, msg)
            if show_warnings:
                messages.add_message(request, messages.WARNING, '{} - AVVISI'.format(i))
                for m in results[2]:
                    messages.add_message(request, messages.WARNING, m)
            if save:
                LogEntry.objects.log_action(user_id         = request.user.pk,
                                            content_type_id = ContentType.objects.get_for_model(i).pk,
                                            object_id       = i.pk,
                                            object_repr     = i.__str__(),
                                            action_flag     = CHANGE,
                                            change_message  = msg)
        except Exception as e:
            messages.add_message(request, messages.ERROR, msg_err.format(i.__str__(), e.__str__()))
            failed += 1
    if num:
        messages.add_message(request, messages.INFO, '{} Punteggi calcolati su un totale di {}'.format(num, failed + num))

def calcolo_punteggio_domanda(modeladmin, request, queryset):
    """
    i.calcolo_punteggio_domanda va a riepire il campo a questo dedicato
    all'interno della domanda
    """
    _calcolo_punteggio_domanda(modeladmin=modeladmin,
                               request=request,
                               queryset=queryset)
calcolo_punteggio_domanda.short_description = "Calcolo automatico del punteggio"


def calcolo_punteggio_domanda_ignora_disabilitati(modeladmin,
                                                  request,
                                                  queryset,
                                                  ignora_disabilitati=True):
    """
    i.calcolo_punteggio_domanda va a riepire il campo a questo dedicato
    all'interno della domanda
    """
    _calcolo_punteggio_domanda(modeladmin=modeladmin,
                               request=request,
                               queryset=queryset,
                               ignora_disabilitati=ignora_disabilitati)
calcolo_punteggio_domanda_ignora_disabilitati.short_description = "Calcolo automatico del punteggio (ignora disabilitati)"


def _download_report_graduatoria(modeladmin,
                                 request,
                                 queryset,
                                 ignora_disabilitati=False):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="{}.csv"'.format(queryset.first().bando)
    return export_graduatoria_csv(queryset=queryset,
                                  fopen=response,
                                  replace_dot_with=',',
                                  ignora_disabilitati=ignora_disabilitati)


def download_report_graduatoria(modeladmin, request, queryset):
    """
    """
    return _download_report_graduatoria(modeladmin=modeladmin,
                                        request=request,
                                        queryset=queryset)
download_report_graduatoria.short_description = "Download report risultati"


def download_report_graduatoria_ignora_disabilitati(modeladmin,
                                                    request,
                                                    queryset):
    """
    """
    return _download_report_graduatoria(modeladmin=modeladmin,
                                        request=request,
                                        queryset=queryset,
                                        ignora_disabilitati=True)
download_report_graduatoria_ignora_disabilitati.short_description = "Download report risultati (ignora disabilitati)"


def progressione_accettata(modeladmin, request, queryset):
    """
    progressione_accettata
    """
    num = 0
    failed = 0
    msg_ok = '{} progressione accettata'
    for i in queryset:
        i.progressione_accettata = 1
        i.dipendente.data_ultima_progressione_manuale = timezone.datetime(i.bando.data_inizio.year,
                                                                          1, 1).date()
        i.dipendente.save()
        i.save()
        messages.add_message(request, messages.INFO, msg_ok.format(i.__str__()))
        num += 1
    if num:
        messages.add_message(request, messages.INFO, '{} progressioni accettate'.format(num))
progressione_accettata.short_description = "Marca come Progressione Accettata"


def verifica_allegati(modeladmin, request, queryset):
    """
    testa se gli allegati inseriti siano realmente presenti sul disco
    check di integrità
    """
    failed = 0
    msg_err = 'Errore in {} {}: {} [{}]'
    for i in queryset:
        for m in i.modulodomandabando_set.all():
            p = m.get_allegati_path()
            if len(p) >= 1:
                p = p[0]
                if not os.path.exists(p):
                    messages.add_message(request, messages.ERROR,
                                         msg_err.format(i, m, p, m.modified))
                    failed += 1
    if failed:
        messages.add_message(request, messages.ERROR, '{} allegati mancanti'.format(failed))
verifica_allegati.short_description = "Verifica allegati"


def verifica_punteggio_domanda(modeladmin, request, queryset):
    """
    i.calcolo_punteggio_domanda va a riepire il campo a questo dedicato
    all'interno della domanda
    """
    _calcolo_punteggio_domanda(modeladmin=modeladmin,
                               request=request,
                               queryset=queryset,
                               save=False,
                               show_warnings=True)
verifica_punteggio_domanda.short_description = "Verifica del punteggio calcolato"


def verifica_punteggio_domanda_ignora_disabilitati(modeladmin,
                                                   request,
                                                   queryset,
                                                   ignora_disabilitati=True):
    """
    i.calcolo_punteggio_domanda va a riepire il campo a questo dedicato
    all'interno della domanda
    """
    _calcolo_punteggio_domanda(modeladmin=modeladmin,
                               request=request,
                               queryset=queryset,
                               save=False,
                               ignora_disabilitati=ignora_disabilitati,
                               show_warnings=True)
verifica_punteggio_domanda_ignora_disabilitati.short_description = "Verifica del punteggio calcolato (ignora disabilitati)"
