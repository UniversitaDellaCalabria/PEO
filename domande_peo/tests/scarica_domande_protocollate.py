import datetime
import os

from domande_peo.models import *
from gestione_peo.models import Bando
from protocollo_ws.protocollo import Protocollo


df = '%d/%m/%Y'
bando = Bando.objects.filter(slug='peo-2018').last()

ws_client = Protocollo()

for i in DomandaBando.objects.filter(bando=bando):
    print(i)
    if not i.is_protocollata():
        print(i, 'non protocollata')
        continue
    ws_client.numero = i.numero_protocollo
    ws_client.anno = 2018
    destdir = '/tmp/peo-2018/{}'.format(i.dipendente.__str__().replace(' ', '_'))
    os.mkdir(destdir)
    ws_client.dump_files(destdir)
