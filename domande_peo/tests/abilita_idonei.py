from gestione_risorse_umane.models import Dipendente
from domande_peo.models import AbilitazioneBandoDipendente
from gestione_peo.models import Bando

b = Bando.objects.last()

for i in l:
    d = Dipendente.objects.get(matricola=i)
    AbilitazioneBandoDipendente.objects.create(bando=b, dipendente=d)
