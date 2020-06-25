from django_form_builder.utils import get_as_dict
from domande_peo.models import *
from gestione_peo.models import *

_motivazione = """Il titolo non è valutabile perchè non si configura come "ulteriore titolo di studio superiore rispetto a quello richiesto per l'accesso dall'esterno"."""

bando = Bando.objects.get(slug='peo-2018')
field_name = 'titolo_di_studio_superiore'

lista_errati = []
salva = False

for dom in DomandaBando.objects.filter(bando=bando):
    dipendente = dom.dipendente
    # pos_eco = dipendente.livello.posizione_economica
    pos_eco = dom.livello.posizione_economica
    punteggio_titoli_pos_eco = bando.get_punteggio_titoli_pos_eco(pos_eco)
    for mdb in dom.modulodomandabando_set.all():
        if mdb.disabilita: continue
        json_dict = json.loads(mdb.modulo_compilato)
        d = get_as_dict(json_dict)
        if field_name in d.keys():
            punteggio =  Punteggio_TitoloStudio.objects.get(pk=d[field_name])
            if punteggio not in punteggio_titoli_pos_eco:
                errato = (dipendente,
                          mdb.descrizione_indicatore,
                          ' - livello {}'.format(pos_eco))
                print(*errato)
                print(bando.punteggio_titolostudio_set.get(pk=d[field_name] ),
                      '::',
                      d.get('etichetta_inserimento'),
                      '::',
                      d.get('rilasciato_da'))
                print()
                lista_errati.append(errato)
                if salva:
                    mdb.disabilita = True
                    mdb.motivazione = _motivazione
                    mdb.save()


