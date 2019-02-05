import datetime
from domande_peo.models import *
from gestione_peo.models import Bando

df = '%d/%m/%Y'
bando = Bando.objects.filter(redazione=True).last()

def print_ad(i):
    print(i.dipendente)
    print(i.dipendente.get_data_progressione().strftime(df))
    print(i.dipendente.get_data_presa_servizio_csa().strftime(df))
    print()
    
ad = AbilitazioneBandoDipendente.objects.all()
for i in ad:
    if not i.dipendente.idoneita_peo():
        print("Non idoneo: ")
        print_ad(i)
        if i.dipendente.idoneita_peo_attivata():
            print('...Ma attivata manualmente da ARU.')
    
    if i.dipendente.get_data_progressione() < i.dipendente.get_data_presa_servizio_csa():
        print("Data progressione inferiore a data presa servizio: ")
        print_ad(i)

    
    if bando.ultima_progressione < i.dipendente.get_data_progressione().date():
        print("L' ultima progressione accettate dal bando ({}) esclude la data di progressione del dipendente : ".format(bando.ultima_progressione))
        print_ad(i)
        
