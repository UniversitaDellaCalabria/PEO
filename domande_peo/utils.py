import csv
import json
import magic
import os
import shutil

from django.apps import apps
from django.conf import settings
from django.contrib import messages
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE
from django.contrib.contenttypes.models import ContentType
from django.http import Http404
from django.http.response import HttpResponse, HttpResponseRedirect
from django.utils import timezone

from django_form_builder.utils import (get_allegati,
                                       get_allegati_dict,
                                       get_as_dict,
                                       get_labeled_errors,
                                       get_POST_as_json,
                                       set_as_dict)

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
                    riga.append(domanda.get_punteggio_anzianita().__str__().replace('.', replace_dot_with))
                    # Punteggio totale
                    riga.append(domanda.punteggio_calcolato.__str__().replace('.', replace_dot_with))
                    writer.writerow(riga)
                    index += 1
            writer.writerow('')
    return fopen


def aggiungi_titolo_form(request,
                         bando,
                         descrizione_indicatore,
                         domanda_bando,
                         dipendente,
                         return_url,
                         log=False):
    form = descrizione_indicatore.get_form(data=request.POST,
                                           files=request.FILES,
                                           domanda_id=domanda_bando.id)
    if form.is_valid():
        # qui chiedere conferma prima del salvataggio
        json_data = get_POST_as_json(request)
        mdb_model = apps.get_model(app_label='domande_peo', model_name='ModuloDomandaBando')
        mdb = mdb_model.objects.create(
                domanda_bando = domanda_bando,
                modulo_compilato = json_data,
                descrizione_indicatore = descrizione_indicatore,
                modified=timezone.localtime(),
                )

        # salvataggio degli allegati nella cartella relativa
        # Ogni file viene rinominato con l'ID del ModuloDomandaBando
        # appena creato e lo "slug" del campo FileField
        # json_stored = mdb.get_as_dict()
        json_dict = json.loads(mdb.modulo_compilato)
        json_stored = get_as_dict(json_dict)
        if request.FILES:
            json_stored["allegati"] = {}
            path_allegati = get_path_allegato(dipendente.matricola,
                                              bando.slug,
                                              mdb.pk)
            for key, value in request.FILES.items():
                salva_file(request.FILES[key],
                            path_allegati,
                            request.FILES[key]._name)
                json_stored["allegati"]["{}".format(key)] = "{}".format(request.FILES[key]._name)

        set_as_dict(mdb, json_stored)
        # mdb.set_as_dict(json_stored)
        domanda_bando.mark_as_modified()
        msg = 'Inserimento {} effettuato con successo!'.format(mdb)
        #Allega il messaggio al redirect
        messages.success(request, msg)
        if log:
            LogEntry.objects.log_action(user_id = request.user.pk,
                                        content_type_id = ContentType.objects.get_for_model(domanda_bando).pk,
                                        object_id       = domanda_bando.pk,
                                        object_repr     = domanda_bando.__str__(),
                                        action_flag     = CHANGE,
                                        change_message  = msg)
        # url = reverse('gestione_peo:commissione_domanda_manage', args=[commissione.pk, domanda_bando.pk,])
        return HttpResponseRedirect(return_url)
    else:
        dictionary = {}
        # il form non è valido, ripetere inserimento
        dictionary['form'] = form
        return dictionary

def modifica_titolo_form(request,
                         bando,
                         descrizione_indicatore,
                         mdb,
                         allegati,
                         path_allegati,
                         return_url,
                         log=False):
    json_response = json.loads(get_POST_as_json(request))
    # Costruisco il form con il json dei dati inviati e tutti gli allegati
    json_response["allegati"] = allegati
    # rimuovo solo gli allegati che sono stati già inseriti
    form = descrizione_indicatore.get_form(data=json_response,
                                           files=request.FILES,
                                           domanda_id=mdb.domanda_bando.id,
                                           remove_filefields=allegati)
    if form.is_valid():
        if request.FILES:
            for key, value in request.FILES.items():
                # form.validate_attachment(request.FILES[key])
                salva_file(request.FILES[key],
                            path_allegati,
                            request.FILES[key]._name)
                nome_allegato = request.FILES[key]._name
                json_response["allegati"]["{}".format(key)] = "{}".format(nome_allegato)
        else:
            # Se non ho aggiornato i miei allegati lasciandoli invariati rispetto
            # all'inserimento precedente
            json_response["allegati"] = allegati

        # salva il modulo
        # mdb.set_as_dict(json_response)
        set_as_dict(mdb, json_response)
        # data di modifica
        mdb.mark_as_modified()
        #Allega il messaggio al redirect
        msg = 'Modifica {} effettuata con successo!'.format(mdb)
        messages.success(request, msg)
        if log:
            LogEntry.objects.log_action(user_id = request.user.pk,
                                        content_type_id = ContentType.objects.get_for_model(mdb.domanda_bando).pk,
                                        object_id       = mdb.domanda_bando.pk,
                                        object_repr     = mdb.domanda_bando.__str__(),
                                        action_flag     = CHANGE,
                                        change_message  = msg)
        return HttpResponseRedirect(return_url)
    else:
        dictionary = {}
        # il form non è valido, ripetere inserimento
        dictionary['form'] = form
        return dictionary

def elimina_allegato_from_mdb(request,
                              bando,
                              dipendente,
                              mdb,
                              allegato,
                              return_url,
                              log=False):
    # json_stored = mdb.get_as_dict()
    json_dict = json.loads(mdb.modulo_compilato)
    json_stored = get_as_dict(json_dict)
    nome_file = json_stored["allegati"]["{}".format(allegato)]

    # Rimuove il riferimento all'allegato dalla base dati
    del json_stored["allegati"]["{}".format(allegato)]

    # mdb.set_as_dict(json_stored)
    set_as_dict(mdb, json_stored)
    mdb.mark_as_modified()
    mdb.domanda_bando.mark_as_modified()

    path_allegato = get_path_allegato(dipendente.matricola,
                                      bando.slug,
                                      mdb.pk)
    # Rimuove l'allegato dal disco
    elimina_file(path_allegato, nome_file)

    msg = 'Allegato {} eliminato con successo da {}'.format(nome_file, mdb)
    if log:
        LogEntry.objects.log_action(user_id = request.user.pk,
                                    content_type_id = ContentType.objects.get_for_model(mdb.domanda_bando).pk,
                                    object_id       = mdb.domanda_bando.pk,
                                    object_repr     = mdb.domanda_bando.__str__(),
                                    action_flag     = CHANGE,
                                    change_message  = msg)
    return HttpResponseRedirect(return_url)

def cancella_titolo_from_domanda(request,
                                 bando,
                                 dipendente,
                                 mdb,
                                 return_url,
                                 mark_domanda_as_modified=True,
                                 log=False):
    mdb.delete()
    if mark_domanda_as_modified:
        mdb.domanda_bando.mark_as_modified()
    # Rimuove la folder relativa al modulo compilato,
    # comprensiva di allegati ('modulo_compilato_id' passato come argomento)
    elimina_directory(dipendente.matricola, bando.slug, mdb.pk)
    msg = 'Modulo {} rimosso con successo!'.format(mdb)
    if log:
        LogEntry.objects.log_action(user_id = request.user.pk,
                                    content_type_id = ContentType.objects.get_for_model(mdb.domanda_bando).pk,
                                    object_id       = mdb.domanda_bando.pk,
                                    object_repr     = mdb.domanda_bando.__str__(),
                                    action_flag     = CHANGE,
                                    change_message  = msg)
    messages.success(request, msg)
    return HttpResponseRedirect(return_url)

def download_allegato_from_mdb(bando,
                               mdb,
                               dipendente,
                               allegato):
    # json_stored = mdb.get_as_dict()
    json_dict = json.loads(mdb.modulo_compilato)
    json_stored = get_as_dict(json_dict)
    nome_file = json_stored["allegati"]["{}".format(allegato)]

    path_allegato = get_path_allegato(dipendente.matricola,
                                      bando.slug,
                                      mdb.pk)
    result = download_file(path_allegato,
                           nome_file)

    if result is None: raise Http404
    return result
