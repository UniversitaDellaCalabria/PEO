import csv
from gestione_risorse_umane.models import Dipendente

f = open('/home/wert/Scrivania/ELENCHI_DEL_PERSONALE_20190131_1424_DATI.csv')

disallineati = []
csvread = csv.DictReader(f, delimiter=';')
for i in csvread:
    d = Dipendente.objects.filter(matricola=i['MATRICOLA']).first()
    if not d:
        print('{} failed'.format(i))
        continue
    if d.get_ruolo_csa() != i['RUOLO']:
        print('{} {} invece che {}'.format(d, d.get_ruolo_csa(), i['RUOLO']))
        disallineati.append((d, i))
