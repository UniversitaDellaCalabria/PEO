from django.conf import settings
from gestione_peo.models import Bando
from domande_peo.models import *
from shutil import copyfile

bando = Bando.objects.last()
base_path = '/'.join((settings.MEDIA_ROOT, settings.DOMANDE_PEO_FOLDER))
backup_folder='/opt/django_peo_dumps/backup_replica/media/media/domande_peo/'
# backup_folder = '/opt/django_peo_dumps/media/media/domande_peo/'
restore=0

failed = []

def test_allegati(bando):
    for i in DomandaBando.objects.filter(bando=bando):
        for m in i.modulodomandabando_set.all():
            p = m.get_allegati_path()
            if len(p) >= 1:
                p = p[0]
                if not os.path.exists(p):
                    print('Errore in {}: {}'.format(i, p))

                    if backup_folder:
                        pp = p.replace(base_path, backup_folder)
                        if not os.path.exists(pp):
                            print('  Non recuperabile: {}'.format(pp))
                            failed.append(pp)
                        else:
                            print('  Recuperabile in: {}'.format(pp))
                            fname = pp.split('/')[-1]
                            bdir = base_path + '/{}/bando-{}'.format(i.dipendente.matricola,
                                                                    bando.slug,)
                            dest_dir =  bdir + '/domanda-id-{}/'.format(m.pk)
                            dest_complete = dest_dir+fname
                            if restore:
                                print('  ... Copy "{}"\n      into: "{}"'.format(pp, dest_complete))
                                if not os.path.exists(bdir):
                                    os.mkdir(bdir)
                                if not os.path.exists(dest_dir):
                                    os.mkdir(dest_dir)
                                copyfile(pp, dest_complete)
