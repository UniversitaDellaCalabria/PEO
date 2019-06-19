from django.conf import settings
from django.core.mail import mail_admins
from django.core.management.base import BaseCommand, CommandError

from csa.models import V_ANAGRAFICA
from gestione_risorse_umane.models import Dipendente

import os

CACHE_DIR='django_peo_cache/'

class Command(BaseCommand):
    help = 'CSA sync with Dipendenti'

    def add_arguments(self, parser):
        parser.add_argument('-debug', required=False, default=True, action="store_true")
        parser.add_argument('-email', required=False,
                            action="store_true", help="Invia una email in caso di errori")

    def handle(self, *args, **options):
        print('CSA_MODE {}'.format(settings.CSA_MODE))
        # if pure replica it will run your custom script
        if settings.CSA_MODE == 'replica':
            print('... Running: {}'.format(settings.CSA_REPL_SCRIPT))
            import importlib
            importlib.import_module(settings.CSA_REPL_SCRIPT)

        # if in native mode it will run cached sync
        # clean previous
        cached = [CACHE_DIR+i for i in os.listdir(CACHE_DIR) if i != 'README.md' and i != 'tmp']
        for i in cached: os.remove(i)

        failed = []
        print('Extracting Anagrafica ...')
        for dcsa in V_ANAGRAFICA.objects.all():
            print('Processing {}'.format(dcsa))
            matricola = dcsa.matricola.lstrip('0')
            dip = Dipendente.objects.filter(matricola=matricola).first()
            if not dip:
                dip = Dipendente.objects.create(matricola=matricola,
                                                nome=dcsa.nome,
                                                cognome=dcsa.cognome,
                                                codice_fiscale=dcsa.cod_fis)
            # else:
                # dip = Dipendente.objects.get(matricola=matricola)
                # dip.nome = dcsa.nome
                # dip.cognome=dcsa.cognome
                # dip.codice_fiscale=dcsa.cod_fis
                # dip.save()
            try:
                dip.sync_csa()
            except Exception as e:
                # ## invia una email
                print('ERRORE csa_sync {}: {}'.format(dcsa, e))
                failed.append(dip)

        self.stdout.write(self.style.SUCCESS('Successfully processed %d Dipendenti' \
                                             % (V_ANAGRAFICA.objects.count() - len(failed))))

        if failed:
            error_msg = 'Errors on %d Dipendenti' % len(failed)
            self.stdout.write(self.style.ERROR(error_msg))
            if options.get('debug'):
                for i in failed:
                    print('Failed:', i)
            if options.get('email'):
                mail_admins('PEO csa_sync:  {}'.format(error_msg),
                            '\n'.join(i for i in failed))
