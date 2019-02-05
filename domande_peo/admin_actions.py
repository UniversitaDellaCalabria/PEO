from django.apps import apps
from django.contrib import messages
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponse

from .models import *
from .utils import export_graduatoria_csv

def calcolo_punteggio_domanda(modeladmin, request, queryset):
    """
    i.calcolo_punteggio_domanda va a riepire il campo a questo dedicato
    all'interno della domanda
    """
    num = 0
    failed = 0
    msg_err = 'Sono incorsi errori nel calcolare {}: {}'
    msg_ok = '{}, punteggio: {}'
    for i in queryset:
        try:
            i.calcolo_punteggio_domanda(save=True)
            num += 1
            messages.add_message(request, messages.INFO, msg_ok.format(i, i.punteggio_calcolato))
        except Exception as e:
            messages.add_message(request, messages.ERROR, msg_err.format(i.__str__(), e.__str__()))
            failed += 1
    if num:
        messages.add_message(request, messages.INFO, '{} Punteggi calcolati su un totale di {}'.format(num, failed + num))

calcolo_punteggio_domanda.short_description = "Calcolo automatico del punteggio"


def download_report_graduatoria(modeladmin, request, queryset):
    """
    """
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="{}.csv"'.format(queryset.first().bando)
    return export_graduatoria_csv(queryset, response, replace_dot_with = ',')

download_report_graduatoria.short_description = "Download report risultati"
