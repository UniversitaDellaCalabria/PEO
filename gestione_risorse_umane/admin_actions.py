from django.apps import apps
from django.contrib import messages
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE
from django.contrib.contenttypes.models import ContentType

from gestione_peo.models import Bando
from .models import *

def abilita_idoneita_peo(modeladmin, request, queryset):
    bando = Bando.objects.filter(redazione=True).last()
    msg_bando_not_valid = ('Nessun Bando attivo. '
                           'Prova a configurare "redazione" '
                           'al Bando di riferimento e a controllare '
                           'che questo non sia scaduto.')
    if not bando:
        messages.add_message(request, messages.ERROR, msg_bando_not_valid)
        return
    elif bando.is_scaduto():
        messages.add_message(request, messages.ERROR, msg_bando_not_valid)
        return
    
    abilitati_peo_model = apps.get_model(app_label='domande_peo',
                                         model_name='AbilitazioneBandoDipendente')
    #dip_pk = []
    for dip in queryset:
        if dip.disattivato:
            messages.add_message(request, messages.ERROR,
                                "Il dipendente {} si trova in stato "
                                "'disattivato'. Per procedere all'abilitazione "
                                " occorre modificare questo parametro".format(dip))
            continue
        #if dip.idoneita_peo():
        messages.add_message(request, messages.INFO,
        '{} idoneo a {}. Dipendente correttamente inserito tra gli abilitati.'.format(dip, bando, ''))
        abilitato = abilitati_peo_model.objects.create(bando=bando, dipendente=dip)
        #dip_pk.append(abilitato.pk)
        # else:
            # messages.add_message(request, messages.WARNING,
                                 # '{} non idoneo a {}'.format(dip, bando))

    # abilitati_preesistenti = abilitati_peo_model.objects.exclude(bando=bando,
                                                                 # dipendente__pk__in=dip_pk)
    # for ap in abilitati_preesistenti:
        # msg = '{} risulta essere abilitato ma non nel calcolo attuale. Verifica se legittimo.'
        # messages.add_message(request, messages.WARNING,
        # msg.format(ap.dipendente))
    
abilita_idoneita_peo.short_description = "Abilita i selezionati a partecipare al Bando in Redazione"

def disabilita_idoneita_peo(modeladmin, request, queryset):
    bando = Bando.objects.filter(redazione=True).last()
    msg_bando_not_valid = ('Nessun Bando attivo. '
                           'Prova a configurare "redazione" '
                           'al Bando di riferimento e a controllare '
                           'che questo non sia scaduto.')
    if not bando:
        messages.add_message(request, messages.ERROR, msg_bando_not_valid)
        return
    elif bando.is_scaduto():
        messages.add_message(request, messages.ERROR, msg_bando_not_valid)
        return
    
    abilitati_peo_model = apps.get_model(app_label='domande_peo',
                                         model_name='AbilitazioneBandoDipendente')
    for dip in queryset:
        #if dip.idoneita_peo():
        messages.add_message(request, messages.WARNING,
        '{} idoneo a {}. Dipendente correttamente rimosso dagli abilitati.'.format(dip, bando, ''))
        abilitato = abilitati_peo_model.objects.filter(bando=bando, dipendente=dip)
        abilitato.delete()
    
disabilita_idoneita_peo.short_description = "Disabilita i selezionati a partecipare al Bando in Redazione"


def sincronizza_da_csa(modeladmin, request, queryset):
    num_sync = 0
    for i in queryset:
        if i.sync_csa():
            num_sync += 1
        else:
            messages.add_message(request, messages.ERROR, 'Sono incorsi errori nel sincronizzare {}'.format(i.__str__()))
    if num_sync:
        messages.add_message(request, messages.INFO, '{} Dipendenti sincronizzati da CSA'.format(num_sync))

sincronizza_da_csa.short_description = "Sincronizza i dati dei dipendenti selezionati da CSA"
