from gestione_risorse_umane.models import Dipendente
import csv

f = open('/home/wert/Scaricati/unatantum.csv')
reader = csv.reader(f, delimiter=',')

failed = []
for i in reader:
    d = Dipendente.objects.filter(matricola=i[0]).first()
    row = ','.join(i)
    if not d:
        print('MANCA: {}'.format(row))
        continue
    check = i[3] == d.affinita_organizzativa.nome.replace('Dipartimento di ', '')
    if not check:
        print('Failed: {}, {} <- {}'.format(d, d.affinita_organizzativa, row))
        failed.append(i)

len(failed)
