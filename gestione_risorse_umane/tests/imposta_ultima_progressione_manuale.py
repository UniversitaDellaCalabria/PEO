import csv
import datetime

from gestione_risorse_umane.models import Dipendente

file = open("/home/francesco/elenco.csv")
reader = csv.reader(file, delimiter=',')
for i in reader:
    d = Dipendente.objects.filter(matricola=i[2]).first()
    if not d:
        print("Matricola non trovata {}".format(i[2]))
        print()
        continue
    prog_csv = datetime.datetime.strptime(i[4], '%d/%m/%Y').date()
    prog_sistema = d.get_data_progressione()
    diff = "Inviariato"
    if prog_sistema != prog_csv:
        diff = "Ultima progressione modificata"
        d.data_ultima_progressione_manuale = prog_csv
        d.save(update_fields=["data_ultima_progressione_manuale",])
    print(d)
    print("Data ultima progressione sistema: ", prog_sistema)
    print("Data ultima progressione file excel: ", prog_csv)
    print(diff)
    print()
