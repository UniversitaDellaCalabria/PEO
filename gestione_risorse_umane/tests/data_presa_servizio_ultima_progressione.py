from django.utils import timezone
from gestione_peo.models import Bando
from gestione_risorse_umane.models import Dipendente
from domande_peo.models import DomandaBando
import csv

_dt_format = '%d/%m/%Y'
f = open('django_peo_cache/f.csv')
reader = csv.DictReader(f)

l = []

f.seek(0)
for i in [ii for ii in reader][1:]:
    print(i['nome'], i['cognome'])
    e = {}
    Dipendente.objects.get(matricola=int(i['matricola']))

    e = {'nome': i['nome'],
         'cognome': i['cognome'],
         'data_presa_servizio': timezone.datetime.strptime(i['data_presa_servizio'], _dt_format),
         'matricola': int(i['matricola']),
         'posizione': i['posizione'],
         'ultima_progressione': timezone.datetime.strptime(i['ultima_progressione'], _dt_format)
         }
    l.append(e)


bando = Bando.objects.last()
domande = DomandaBando.objects.filter(bando=bando)

# update domande e dipendenti
for i in l:
    dipendente = Dipendente.objects.get(matricola=i['matricola'])
    print(dipendente)
    dipendente.data_presa_servizio_manuale = i['data_presa_servizio']
    dipendente.data_ultima_progressione_manuale = i['ultima_progressione']
    dipendente.save()
    domanda = domande.filter(dipendente__matricola=i['matricola']).first()
    if not domanda: continue
    print(domanda,
          (domanda.data_presa_servizio, i['data_presa_servizio']),
          (domanda.data_ultima_progressione, i['ultima_progressione']))
    domanda.data_presa_servizio = i['data_presa_servizio']
    domanda.data_ultima_progressione = i['ultima_progressione']
    domanda.save()
