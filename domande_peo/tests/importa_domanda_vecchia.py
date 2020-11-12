import json

from domande_peo.models import *
from gestione_peo.models import *


def migra_domanda_vecchia(domanda_vecchia_pk='', domanda_nuova_pk='', debug=1):
    bando_vecchio = Bando.objects.all()[2]
    domanda_vecchia = DomandaBando.objects.get(pk=domanda_vecchia_pk)
    domanda_nuova = DomandaBando.objects.get(pk=domanda_nuova_pk)

    for i in domanda_vecchia.modulodomandabando_set.filter(disabilita__in=(False, None)):
        nd = i.__dict__
        del(nd['_state'])
        nd['domanda_bando_id'] = domanda_nuova.pk
        nd['punteggio_calcolato'] = None
        del(nd['id'])
        del(nd['created'])
        del(nd['modified'])
        nd['modulo_compilato'] = json.loads(nd['modulo_compilato'])
        nd['modulo_compilato']['domanda_bando_id'] = domanda_nuova.pk


        desc_ind_vecchio = DescrizioneIndicatore.objects.get(pk=nd['descrizione_indicatore_id'])
        indicatore_ponderato = IndicatorePonderato.objects.get(bando=domanda_nuova.bando,
                                                               id_code=desc_ind_vecchio.indicatore_ponderato.id_code)
        desc_ind_nuovo = DescrizioneIndicatore.objects.get(indicatore_ponderato=indicatore_ponderato,
                                                           id_code=desc_ind_vecchio.id_code)

        if nd['modulo_compilato'].get('sub_descrizione_indicatore'):
            subdesk_vecchio = SubDescrizioneIndicatore.objects.get(pk = nd['modulo_compilato']['sub_descrizione_indicatore'])
            subdesk_nuovo   = SubDescrizioneIndicatore.objects.get(id_code = subdesk_vecchio.id_code,
                                                                   descrizione_indicatore_id = desc_ind_nuovo)
            print(subdesk_vecchio, subdesk_nuovo)

            nd['modulo_compilato']['sub_descrizione_indicatore'] = subdesk_nuovo.pk

        nd['modulo_compilato'] = json.dumps(nd['modulo_compilato'])
        nd['descrizione_indicatore_id'] = desc_ind_nuovo.pk

        if debug:
            print(nd)
            print()
        else:
            ModuloDomandaBando.objects.create(**nd)

migra_domanda_vecchia(domanda_nuova_pk=that_pk, domanda_vecchia_pk=that_pk, debug=1)
