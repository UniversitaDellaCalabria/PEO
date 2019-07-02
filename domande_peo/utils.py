import csv
import magic
import os
import shutil

from django.apps import apps
from django.conf import settings
from django.http.response import HttpResponse

from gestione_peo.models import Bando, IndicatorePonderato, DescrizioneIndicatore
from gestione_risorse_umane.models import Dipendente, PosizioneEconomica, LivelloPosizioneEconomica

def get_fname_allegato(domanda_bando_id, bando_id):
    return "domanda_{}-{}.pdf".format(domanda_bando_id, bando_id)

def get_path_allegato(matricola, slug_bando, id_modulo_inserito):
    """
        Costruisce il path dei file relativi agli allegati e lo restituisce
    """
    path = '{}/{}/{}/bando-{}/domanda-id-{}'.format(settings.MEDIA_ROOT,
                                                    settings.DOMANDE_PEO_FOLDER,
                                                    matricola,
                                                    slug_bando,
                                                    id_modulo_inserito)
    return path

def salva_file(f, path, nome_file):
    file_path = '{}/{}'.format(path,nome_file)

    if not os.path.exists(os.path.dirname(file_path)):
        os.makedirs(os.path.dirname(file_path))
    with open(file_path,'wb') as destination:
        for chunk in f.chunks():
            destination.write(chunk)

def download_file(path, nome_file):
    """
        Effettua il download di un file
    """
    mime = magic.Magic(mime=True)
    file_path = '{}/{}'.format(path,nome_file)
    content_type = mime.from_file(file_path)

    if os.path.exists(file_path):
        with open(file_path, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type=content_type)
            response['Content-Disposition'] = 'inline; filename=' + os.path.basename(file_path)
            return response
    return None

def elimina_file(path, nome_file):
    """
        Elimina un file allegato a una domanda dal disco
    """

    file_path = '{}/{}'.format(path,nome_file)
    try:
        os.remove(file_path)
        return path
    except:
        return False

def elimina_directory(matricola, bando_slug, modulo_compilato_id = None):
    """
        Rimuove dal disco ricorsivamente una cartella.
        Se il parametro 'modulo_compilato_id' NON viene fornito, la funzione
        cancella la directory 'matricola' che raccoglie gli allegati della Domanda PEO.
        Se, invece, il parametro viene fornito, allora verrà cancellata solo
        la directory con gli allegati del ModuloCompilato.
    """
    path = '{}/{}/{}/bando-{}'.format(settings.MEDIA_ROOT,
                                               settings.DOMANDE_PEO_FOLDER,
                                               matricola,
                                               bando_slug)
    if modulo_compilato_id:
        path = path + '/domanda-id-{}'.format(modulo_compilato_id)

    try:
        shutil.rmtree(path)
        return path
    except:
        return False


def export_graduatoria_csv(queryset, fopen,
                           delimiter=';', quotechar='"',
                           replace_dot_with = '.'):
    """
    Esporta la graduatoria dei partecipanti,
    fopen può essere un oggetto response oppure un fopen
    """
    # domande_bando selezionate
    queryset = queryset.order_by('-punteggio_calcolato')
    posizioni_economiche = PosizioneEconomica.objects.all().order_by('nome')
    #Recupero tutti i DescrInd del bando in questione
    descr_ind = DescrizioneIndicatore.objects.filter(indicatore_ponderato__bando = queryset.first().bando).all().order_by('id_code')

    intestazione = ['Prog', 'Cognome', 'Nome', 'Pos.Eco']

    writer = csv.writer(fopen,
                        delimiter = delimiter,
                        quotechar = quotechar)
    intestazione2 = []
    lista_id_descr = []
    # Creo le colonne dell'intestazione (Nome + ID code)
    for di in descr_ind:
        if di.calcolo_punteggio_automatico:
            intestazione2.append('({}) {}'.format(di.id_code, di.nome))
            lista_id_descr.append(di.id_code)
    intestazione += intestazione2
    intestazione.append('Anzianità presso Università')
    intestazione.append('Punti')
    writer.writerow(intestazione)

    # Per ogni posizione economica, controllo se ci sono domande
    # cosi da ordinarle e avere una graduatoria
    for pos_eco in posizioni_economiche:
        livelli = LivelloPosizioneEconomica.objects.filter(posizione_economica = pos_eco).all().order_by('nome')
        for livello in livelli:
            writer.writerow('')
            index = 1
            # Per ogni domanda del bando, recupero quelle fatte per
            # un singolo Livello Economico
            for domanda in queryset:
                # Se la domanda non è stata chiusa almeno una volta
                if not domanda.numero_protocollo:
                    continue
                if domanda.dipendente.livello == livello:
                    riga = [index,
                            domanda.dipendente.cognome,
                            domanda.dipendente.nome,
                            livello.__str__()]
                    # Per ogni DescrInd nell'intestazione
                    for descr in lista_id_descr:
                        # Recupero l'oggetto
                        d = descr_ind.filter(id_code = descr).first()
                        # Recupero il punteggio max assegnato nella domanda
                        punteggio = domanda.calcolo_punteggio_max_descr_ind(d, domanda.dipendente.livello)
                        riga.append(punteggio.__str__().replace('.', replace_dot_with))
                    # Anzianità Dipendente Università
                    riga.append(domanda.punteggio_anzianita.replace('.', replace_dot_with))
                    # Punteggio totale
                    riga.append(domanda.punteggio_calcolato.__str__().replace('.', replace_dot_with))
                    writer.writerow(riga)
                    index += 1
            writer.writerow('')
    return fopen
