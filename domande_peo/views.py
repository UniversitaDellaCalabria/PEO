# © 2018 Giuseppe De Marco <giuseppe.demarco@unical.it>
# © 2018 Francesco Filicetti <francesco.filicetti@unical.it>

# SPDX-License-Identifier: GPL-3.0

from django.conf import settings
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.core.mail import send_mail
from django.db.models import Q
from django.http import Http404
from django.http.response import HttpResponse
from django.http.response import HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404, render
from django.urls import reverse
from django.utils.http import is_safe_url
from django.utils import timezone

from django_form_builder.models import SavedFormContent
from django_form_builder.utils import (get_allegati,
                                       get_allegati_dict,
                                       get_as_dict,
                                       get_labeled_errors,
                                       get_POST_as_json,
                                       set_as_dict)
from gestione_peo.decorators import _get_bando_queryset, check_accessibilita_bando, check_termini_domande
from gestione_peo.models import *
from gestione_risorse_umane.models import Dipendente
from unical_template.breadcrumbs import BreadCrumbs
from unical_template.pdf_utils import response_as_pdf

from .decorators import (abilitato_a_partecipare,
                         domanda_modificabile,
                         domanda_cancellabile,
                         modulo_compilato_cancellabile)
from .forms import *
from .models import *
from .utils import *

# pdfs
from PyPDF2 import PdfFileMerger
from io import StringIO, BytesIO

import gestione_peo.settings
import json
import magic
import shutil

_breadcrumbs = BreadCrumbs()

@login_required
#@check_accessibilita_bando
#@check_termini_domande
@abilitato_a_partecipare
def dashboard_domanda(request, bando_id):
    """
        Pagina di gestione della propria domanda.
    """

    dipendente = get_object_or_404(Dipendente, matricola=request.user.matricola)
    bando = _get_bando_queryset(bando_id).first()

    # recupero la domanda peo del dipendente
    domanda_peo = DomandaBando.objects.filter(bando=bando,
                                              dipendente=dipendente)

    # se non c'è alcuna domanda, la creo
    # se la domanda c'è ma is_active==False, ritorno un messaggio di errore
    # altrimenti si prosegue con la domanda attualmente presente
    if domanda_peo:
        domanda_peo = domanda_peo.last()
    elif not domanda_peo:
        url = reverse('domande_peo:scelta_titolo_da_aggiungere',
                      args=[bando.slug])
        return HttpResponseRedirect(url)

    if not domanda_peo.modulodomandabando_set.all() and not domanda_peo.bando.indicatore_con_anzianita():
        url = reverse('domande_peo:scelta_titolo_da_aggiungere',
                      args=[bando.slug])
        return HttpResponseRedirect(url)

    if not domanda_peo.is_active:
        return render(request, 'custom_message.html',
                      {'avviso': ("La tua Domanda è stata sospesa. Per avere "
                                  "informazioni contatta l' Area Risorse Umane.")})

    page_title = 'Partecipazione Bando {}'.format(bando.nome)
    page_url = reverse('domande_peo:dashboard_domanda',
                       args=[bando.slug])
    _breadcrumbs.reset()
    _breadcrumbs.add_url((page_url, page_title))

    context = {'page_title': page_title,
               'breadcrumbs': _breadcrumbs,
               'bando': bando,
               'dipendente': dipendente,
               'domanda_peo': domanda_peo}
    return render(request, "dashboard_domanda.html",context=context)


@login_required
@check_accessibilita_bando
@check_termini_domande
@abilitato_a_partecipare
def scelta_titolo_da_aggiungere(request, bando_id):
    """
        Lista degli indicatori ponderati.
        L'utente sceglie che tipologia di titolo deve aggiungere
    """

    dipendente = get_object_or_404(Dipendente, matricola=request.user.matricola)
    bando = _get_bando_queryset(bando_id).first()
    indicatori_ponderati = bando.indicatoreponderato_set.all().order_by('id_code')
    # recupero la domanda peo del dipendente
    domanda_peo = DomandaBando.objects.filter(bando=bando,
                                              dipendente=dipendente)

    # se non c'è alcuna domanda, la creo
    # se la domanda c'è ma is_active==False, ritorno un messaggio di errore
    # altrimenti si prosegue con la domanda attualmente presente
    if domanda_peo:
        domanda_peo = domanda_peo.last()
    elif not domanda_peo:
        domanda_peo = DomandaBando.objects.create(bando=bando,
                                                  dipendente=dipendente,
                                                  modified=timezone.localtime())
    if not domanda_peo.is_active:
        return render(request, 'custom_message.html',
                      {'avviso': ("La tua Domanda è stata sospesa. Per avere "
                                  "informazioni contatta l' Area Risorse Umane.")})

    #categorie_titoli = CategoriaTitolo.objects.filter(Bando=Bando_id).order_by('ordinamento')


    dashboard_domanda_title = 'Partecipazione Bando {}'.format(bando.nome)
    dashboard_domanda_url = reverse('domande_peo:dashboard_domanda',
                                    args=[bando.slug])

    page_title = 'Selezione Modulo di Inserimento'

    _breadcrumbs.reset()
    _breadcrumbs.add_url((dashboard_domanda_url, dashboard_domanda_title))
    _breadcrumbs.add_url(('#', page_title))

    context = {
        'page_title': page_title,
        'breadcrumbs': _breadcrumbs,
        'bando': bando,
        'dipendente': dipendente,
        'domanda_peo': domanda_peo,
        'indicatori_ponderati': indicatori_ponderati,
        #"categorie_titoli": categorie_titoli,
    }
    return render(request, "scelta_titolo_da_aggiungere.html",context=context)

@staff_member_required
def anteprima_modulo_inserimento(request, bando_id, descrizione_indicatore_id):
    """
        usato in admin per avere una anteprima dei campi scelti
    """

    descrizione_indicatore = get_object_or_404(DescrizioneIndicatore, pk=descrizione_indicatore_id)
    bando = get_object_or_404(Bando, pk=bando_id)
    dipendente = Dipendente.objects.filter(matricola=request.user.matricola).first()

    form = descrizione_indicatore.get_form()

    if request.method == 'POST':
        form = descrizione_indicatore.get_form(data=request.POST)

    page_title = 'Modulo Inserimento: "({}) {}"'.format(descrizione_indicatore.id_code,
                                                          descrizione_indicatore.nome)

    d = {'page_title': page_title,
         'form': form,
         'bando': bando,
         'descrizione_indicatore': descrizione_indicatore,
         'dipendente': dipendente}

    return render(request, 'modulo_form_readonly.html', d)

@login_required
def anteprima_modulo_inserimento_frontend(request, bando_id, descrizione_indicatore_id):
    """
        usato in admin per avere una anteprima dei campi scelti
    """
    descrizione_indicatore = get_object_or_404(DescrizioneIndicatore, pk=descrizione_indicatore_id)
    bando = get_object_or_404(Bando, pk=bando_id)
    dipendente = Dipendente.objects.filter(matricola=request.user.matricola).first()
    form = descrizione_indicatore.get_form()
    if request.method == 'POST':
        form = descrizione_indicatore.get_form(data=request.POST)
    page_title = 'Modulo Inserimento: "({}) {}"'.format(descrizione_indicatore.id_code,
                                                          descrizione_indicatore.nome)
    d = {'page_title': page_title,
         'form': form,
         'bando': bando,
         'descrizione_indicatore': descrizione_indicatore,
         'dipendente': dipendente}
    messages.warning(request, "Questa è esclusivamente un'anteprima"
                  " del modulo di inserimento e non ha alcun effetto"
                  " sulla domanda")
    return render(request, 'modulo_form_readonly_frontend.html', d)

# @login_required
@staff_member_required
def vedi_modulo_inserito(request, bando_id, modulo_domanda_bando_id):
    """
        usato in admin per avere una anteprima dei campi scelti
    """
    modulo_domanda_bando = get_object_or_404(ModuloDomandaBando, pk=modulo_domanda_bando_id)

    bando = get_object_or_404(Bando, pk=bando_id)

    descrizione_indicatore = modulo_domanda_bando.descrizione_indicatore
    # data = modulo_domanda_bando.get_as_dict(allegati=False)
    json_dict = json.loads(modulo_domanda_bando.modulo_compilato)
    data = get_as_dict(json_dict, allegati=False)
    # form = modulo_domanda_bando.compiled_form_readonly(show_title=True)+
    form = SavedFormContent.compiled_form_readonly(modulo_domanda_bando.get_form())
    # allegati = modulo_domanda_bando.get_allegati_dict()
    allegati = get_allegati_dict(modulo_domanda_bando)
    d = {
         'allegati': allegati,
         'form': form,
         'bando': bando,
         'descrizione_indicatore': descrizione_indicatore,
         'modulo_domanda_bando': modulo_domanda_bando,
         'readonly': True}

    return render(request, 'modulo_form_readonly_user.html', d)


@login_required
#@check_accessibilita_bando
#@check_termini_domande
@abilitato_a_partecipare
def accetta_condizioni_bando(request, bando_id):
    """
        Mostra la schermata di accettazione delle condizioni per la
        partecipazione al Bando PEO.
        Accettando le condizioni e proseguendo, viene creata un'istanza
        di Domanda PEO
    """
    dipendente = get_object_or_404(Dipendente,
                                   matricola=request.user.matricola)
    bando = _get_bando_queryset(bando_id).first()

    # se la domanda già esiste fare redirect!
    domanda_bando = DomandaBando.objects.filter(dipendente=dipendente,
                                                bando=bando)
    if domanda_bando:
        url = reverse('domande_peo:dashboard_domanda',
                      args=[domanda_bando.first().bando.slug])
        return HttpResponseRedirect(url)
    # else:
        # raise PermissionDenied(("La tua Domanda di partecipazione non "
                                # "esiste oppure è stata disabilitata."))

    if request.method == 'POST':
        form = AccettazioneClausoleForm(request.POST)
        if form.is_valid():
            conferma = request.POST["accettazione"]
            if conferma:
                url = reverse('domande_peo:dashboard_domanda', args=[bando.slug,])
                return HttpResponseRedirect(url)
            else:
                url = reverse('domande_peo:accetta_condizioni_bando', args=[bando.slug,])
                return HttpResponseRedirect(url)
    else:
        form = AccettazioneClausoleForm()

    page_title = 'Partecipazione Bando {}'.format(bando.nome)
    page_url = reverse('domande_peo:dashboard_domanda',
                      args=[bando.slug])
    _breadcrumbs.reset()
    _breadcrumbs.add_url((page_url, page_title))

    d = {
         'page_title': page_title,
         'breadcrumbs': _breadcrumbs,
         'bando':bando,
         'dipendente': dipendente,
         'form': form}

    return render(request, 'accetta_condizioni_bando.html', d)


@login_required
@check_accessibilita_bando
@check_termini_domande
@abilitato_a_partecipare
@domanda_modificabile
def aggiungi_titolo(request, bando_id, descrizione_indicatore_id):
    """
        Costruisce form da PeodynamicForm
        li valida e salva i dati all'occorrenza
    """
    dipendente = get_object_or_404(Dipendente, matricola = request.user.matricola)
    bando = _get_bando_queryset(bando_id).first()
    domanda_bando = get_object_or_404(DomandaBando,
                                      bando = bando,
                                      dipendente=dipendente,
                                      is_active=True)
    descrizione_indicatore = get_object_or_404(DescrizioneIndicatore,
                                               pk = descrizione_indicatore_id)

    # From gestione_peo/templatetags/indicatori_ponderati_tags
    if not descrizione_indicatore.is_available_for_cat_role(dipendente.livello.posizione_economica,
                                                          dipendente.ruolo):
        return render(request, 'custom_message.html',
                      {'avviso': ("La tua posizione o il tuo ruolo"
                                  " risultano disabilitati"
                                  " all'accesso a questo modulo.")})

    # From domande_peo/templatetags/domande_peo_tags
    if descrizione_indicatore.limite_inserimenti:
        mdb_presenti = domanda_bando.num_mdb_tipo_inseriti(descrizione_indicatore)
        if mdb_presenti == descrizione_indicatore.numero_inserimenti:
            return render(request, 'custom_message.html',
                          {'avviso': ("Hai raggiunto il numero di inserimenti"
                                      " consentiti per questo modulo")})

    form = descrizione_indicatore.get_form(data=None,
                                           files=None,
                                           domanda_id=domanda_bando.id)

    dashboard_domanda_title = 'Partecipazione Bando {}'.format(bando.nome)
    dashboard_domanda_url = reverse('domande_peo:dashboard_domanda',
                                    args=[bando.slug])
    selezione_titolo_title = 'Selezione Modulo di Inserimento'
    selezione_titolo_url = reverse('domande_peo:scelta_titolo_da_aggiungere',
                                   args=[bando.slug])
    page_title = 'Modulo Inserimento: "({}) {}"'.format(descrizione_indicatore.id_code,
                                                          descrizione_indicatore.nome)
    _breadcrumbs.reset()
    _breadcrumbs.add_url((dashboard_domanda_url, dashboard_domanda_title))
    _breadcrumbs.add_url((selezione_titolo_url, selezione_titolo_title))
    _breadcrumbs.add_url(('#', page_title))

    d = {'page_title': page_title,
         'breadcrumbs': _breadcrumbs,
         'form': form,
         'bando':bando,
         'dipendente': dipendente,
         'descrizione_indicatore': descrizione_indicatore}

    if request.method == 'POST':
        form = descrizione_indicatore.get_form(data=request.POST,
                                               files=request.FILES,
                                               domanda_id=domanda_bando.id)
        if form.is_valid():
            # qui chiedere conferma prima del salvataggio
            json_data = get_POST_as_json(request)
            mdb = ModuloDomandaBando.objects.create(
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
            #Allega il messaggio al redirect
            messages.success(request, 'Inserimento effettuato con successo!')

            url = reverse('domande_peo:dashboard_domanda', args=[bando.pk,])
            return HttpResponseRedirect(url+'#{}'.format(bando.slug))
        else:
            # il form non è valido, ripetere inserimento
            d['form'] = form
            d['labeled_errors'] = get_labeled_errors(form)
            # print('ERRORE', request.POST)

    return render(request, 'modulo_form.html', d)

@login_required
@check_accessibilita_bando
@check_termini_domande
@abilitato_a_partecipare
@domanda_modificabile
def modifica_titolo(request, bando_id,
                    modulo_compilato_id):
    """
        Costruisce form da PeodynamicForm
        li valida e salva i dati all'occorrenza

        remove_filefields prende il valore che concorre a selezionare il template readonly
        usato per readonly=pdf, inoltre rimuove i filefields dal form
    """
    dipendente = get_object_or_404(Dipendente, matricola=request.user.matricola)
    bando = _get_bando_queryset(bando_id).first()

    mdb = get_object_or_404(ModuloDomandaBando,
                            pk=modulo_compilato_id,
                            domanda_bando__is_active=True)

    # json_data = mdb.get_as_dict(allegati=False)
    descrizione_indicatore = mdb.descrizione_indicatore

    # Creo il form con i campi files=None e remove_filefields=False
    # perchè al momento della creazione non ci sono ovviamente allegati
    # già inseriti (ma se non setto remove_filefields=False il form
    # viene generato senza campi FileField)
    # form = mdb.compiled_form(files=None, remove_filefields=False)
    allegati = get_allegati_dict(mdb)
    form = mdb.compiled_form(remove_filefields=allegati)
    # form con i soli campi File da dare in pasto al tag della firma digitale
    form_allegati = descrizione_indicatore.get_form(remove_datafields=True)
    # allegati = mdb.get_allegati_dict()

    # se non ci sono allegati preesistenti evita di distruggere il campo per
    # l'eventuale inserimento di un allegato
    # if allegati:
        # form.remove_files(allegati)

    # Nonostante sia reperibile anche da 'modulo_domanda_bando',
    # nel contesto devo passare anche 'descrizione_indicatore', altrimenti
    # nel breadcrumb di modulo_form.html non riesco a recuperare il nome.
    # Potrei anche duplicare la porzione di html del breadcrumb in modulo_form_modifica.html,
    # è indifferente

    dashboard_domanda_title = 'Partecipazione Bando {}'.format(bando.nome)
    dashboard_domanda_url = reverse('domande_peo:dashboard_domanda',
                                    args=[bando.slug])

    path_allegati = get_path_allegato(dipendente.matricola,
                                      bando.slug,
                                      mdb.pk)

    page_title = 'Modifica Inserimento: "({}) {}"'.format(descrizione_indicatore.id_code,
                                                          descrizione_indicatore.nome)

    _breadcrumbs.reset()
    _breadcrumbs.add_url((dashboard_domanda_url, dashboard_domanda_title))
    _breadcrumbs.add_url(('#', page_title))

    d = {
         'allegati': allegati,
         'bando': bando,
         'breadcrumbs': _breadcrumbs,
         'dipendente': dipendente,
         'form': form,
         'form_allegati': form_allegati,
         'modulo_domanda_bando': mdb,
         'page_title': page_title,
         'path_allegati': path_allegati,
         }

    if request.method == 'POST':
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
            messages.success(request, 'Modifica effettuata con successo!')
            url = reverse('domande_peo:modifica_titolo',
                          args=[bando.pk,modulo_compilato_id])
            return HttpResponseRedirect(url+'#{}'.format(bando.slug))
        else:
            # il form non è valido, ripetere inserimento
            d['form'] = form

    d['labeled_errors'] = get_labeled_errors(form)

    return render(request, 'modulo_form_modifica.html', d)


@login_required
@check_accessibilita_bando
@check_termini_domande
@abilitato_a_partecipare
@domanda_modificabile
@modulo_compilato_cancellabile
def cancella_titolo(request, bando_id, modulo_compilato_id):
    """
        Deve essere chiamato da una dialog con checkbox di conferma
    """

    dipendente = get_object_or_404(Dipendente, matricola = request.user.matricola)
    bando = _get_bando_queryset(bando_id).first()

    mdb = get_object_or_404(ModuloDomandaBando,
                            pk=modulo_compilato_id,
                            domanda_bando__is_active=True,
                            domanda_bando__dipendente=dipendente)

    mdb.delete()
    mdb.domanda_bando.mark_as_modified()
    # Rimuove la folder relativa al modulo compilato,
    # comprensiva di allegati ('modulo_compilato_id' passato come argomento)
    elimina_directory(request.user.matricola, bando.slug, modulo_compilato_id)

    messages.success(request, 'Modulo rimosso con successo!')
    url = reverse('domande_peo:dashboard_domanda', args=[bando.pk,])
    return HttpResponseRedirect(url+'#{}'.format(bando.slug))


@login_required
@check_accessibilita_bando
@abilitato_a_partecipare
@domanda_modificabile
@domanda_cancellabile
def cancella_domanda(request, bando_id, domanda_bando_id):
    """
        Deve essere chiamato da una dialog con checkbox di conferma
    """
    dipendente = get_object_or_404(Dipendente, matricola=request.user.matricola)
    bando = _get_bando_queryset(bando_id).first()

    domanda_bando = get_object_or_404(DomandaBando,
                                      pk=domanda_bando_id,
                                      dipendente=dipendente,
                                      is_active=True)

    domanda_bando.delete()

    # Rimuove la folder relativa alla DomandaPEO del dipendente, dello specifico Bando,
    # comprensiva di allegati ('modulo_compilato_id' NON passato come argomento)
    elimina_directory(request.user.matricola, bando.slug)

    url = reverse('risorse_umane:dashboard')
    return HttpResponseRedirect(url)


@login_required
@check_accessibilita_bando
@check_termini_domande
@abilitato_a_partecipare
@domanda_modificabile
def elimina_allegato(request, bando_id, modulo_compilato_id, allegato):
    """
        Deve essere chiamato da una dialog con checkbox di conferma
    """
    dipendente = get_object_or_404(Dipendente, matricola=request.user.matricola)
    mdb = get_object_or_404(ModuloDomandaBando,
                            pk=modulo_compilato_id,
                            domanda_bando__is_active=True,
                            domanda_bando__dipendente=dipendente)

    bando = mdb.domanda_bando.bando

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
                                       bando_id,
                                       modulo_compilato_id)
    # Rimuove l'allegato dal disco
    elimina_file(path_allegato,
                  nome_file)

    url = reverse('domande_peo:modifica_titolo', args=[bando.id, mdb.id])
    return HttpResponseRedirect(url+'#{}'.format(bando.slug))


@login_required
@abilitato_a_partecipare
def download_allegato(request, bando_id, modulo_compilato_id, allegato):
    """
        Download del file allegato, dopo aver superato i check di proprietà
    """
    # se scarica un utente staff può accedervi
    if request.user.is_staff:
        mdb = get_object_or_404(ModuloDomandaBando,
                                pk=modulo_compilato_id)
        dipendente = get_object_or_404(Dipendente, matricola = mdb.domanda_bando.dipendente.matricola)
    # altrimenti solo se l'utente è il proprietario e la domanda è attiva
    else:
        dipendente = get_object_or_404(Dipendente, matricola = request.user.matricola)
        mdb = get_object_or_404(ModuloDomandaBando,
                                pk=modulo_compilato_id,
                                domanda_bando__is_active=True,
                                domanda_bando__dipendente=dipendente)

    bando = mdb.domanda_bando.bando

    # json_stored = mdb.get_as_dict()
    json_dict = json.loads(mdb.modulo_compilato)
    json_stored = get_as_dict(json_dict)
    nome_file = json_stored["allegati"]["{}".format(allegato)]

    path_allegato = get_path_allegato(dipendente.matricola,
                                      bando.slug,
                                      modulo_compilato_id)
    result = download_file(path_allegato,
                           nome_file)

    if result is None:
        raise Http404
    return result

@login_required
def riepilogo_domanda(request, bando_id, domanda_bando_id, pdf=None):
    """
        Esegue l'output in pdf
    """
    if request.user.is_staff:
        # has the permission to view others data
        domanda_bando = get_object_or_404(DomandaBando,
                                  pk=domanda_bando_id)
    else:
        dipendente = get_object_or_404(Dipendente,
                                       matricola=request.user.matricola)
        domanda_bando = get_object_or_404(DomandaBando,
                                          pk=domanda_bando_id,
                                          dipendente=dipendente,
                                          is_active=True)
    bando = domanda_bando.bando
    page_title = 'Riepilogo Domanda'
    dashboard_domanda_title = 'Partecipazione Bando {}'.format(bando.nome)
    dashboard_domanda_url = reverse('domande_peo:dashboard_domanda',
                                    args=[bando.slug])

    _breadcrumbs.reset()
    _breadcrumbs.add_url((dashboard_domanda_url, dashboard_domanda_title))
    _breadcrumbs.add_url(('#', page_title))

    d = {'page_title': page_title,
        'breadcrumbs': _breadcrumbs,
        'bando': bando,
        'dipendente': domanda_bando.dipendente,
        'domanda_peo': domanda_bando,
        'MEDIA_URL': settings.MEDIA_URL}
    if pdf:
        return render(request, 'riepilogo_domanda_pdf.html', d)
    else:
        return render(request, 'riepilogo_domanda.html', d)

@login_required
def download_modulo_inserito_pdf(request, bando_id, modulo_compilato_id):
    """
        Esegue l'output in pdf
        riutilizzando le view precedenti evitiamo di rifare gli stessi controlli
        ricicliamo query e decoratori
    """
    dipendente = get_object_or_404(Dipendente, matricola=request.user.matricola)
    bando = _get_bando_queryset(bando_id).first()
    mdb = get_object_or_404(ModuloDomandaBando,
                            pk=modulo_compilato_id)
    # se l'utente non fa parte dello staff e il pdf non gli appartiene nega l'accesso
    if not request.user.is_staff:
        mdb = ModuloDomandaBando.objects.filter(domanda_bando__dipendente=dipendente).first()
        if not mdb:
            return 404()

    descrizione_indicatore = mdb.descrizione_indicatore
    form = mdb.compiled_form(remove_filefields=True)
    d = {'form': form,
         'dipendente': dipendente,
         'bando': bando,
         'modulo_domanda_bando': mdb,
         'descrizione_indicatore': descrizione_indicatore}

    response = render(request, 'modulo_form_readonly_pdf.html', d)
    # file names
    pdf_fname = 'modulo_inserito_{}.pdf'.format(mdb.pk)
    pdf_path = settings.TMP_DIR + os.path.sep + pdf_fname

    # prendo il pdf principale
    main_pdf_file = response_as_pdf(response, pdf_fname).content
    merger = PdfFileMerger(strict = False)
    main_pdf_file = BytesIO(main_pdf_file)
    merger.append(main_pdf_file)
    try:
        # gli appendo gli allegati
        for allegato in mdb.get_allegati_path():
            merger.append(allegato)
        merger.write(pdf_path)

        # torno il tutto in response
        f = open(pdf_path, 'rb')
        response = HttpResponse(f.read(), content_type='application/pdf')
        response['Content-Disposition'] = 'inline; filename=' + pdf_fname
    except Exception as e:
        #mdb_dict = mdb.get_as_dict()
        json_dict = json.loads(mdb.modulo_compilato)
        mdb_dict = get_as_dict(json_dict)
        return render(request, 'custom_message.html',
                      {'avviso': ("E' stato incorso un errore relativo alla interpretazione "
                                  "dei file PDF da te immessi come allegato.<br>"
                                  "Nello specifico: '{}' presenta delle anomalie di formato"
                                  ". Questo è dovuto "
                                  "al processo di produzione "
                                  "del PDF. <br>E' necessario ricreare il PDF "
                                  "con una procedura differente da quella "
                                  "precedenemente utilizzata oppure, più "
                                  "semplicemente, ristampare il PDF come file, "
                                  "rimuovere il vecchio allegato dal modulo inserito "
                                  "e caricare il nuovo appena ristampato/riconvertito."
                                  ).format(mdb_dict.get('allegati'))})
    # pulizia
    f.close()
    main_pdf_file.close()
    os.remove(pdf_path)
    return response

@login_required
def download_domanda_pdf(request, bando_id, domanda_bando_id):
    """
    Esegue l'output in pdf
    non ha bisogno di decoratori perchè chiama al suo interno una funzione
    decorata
    """
    response = riepilogo_domanda(request, bando_id,
                                 domanda_bando_id, pdf=True)
    pdf_fname = get_fname_allegato(domanda_bando_id, bando_id)
    return response_as_pdf(response, pdf_fname)

@login_required
@check_accessibilita_bando
@abilitato_a_partecipare
def chiudi_apri_domanda(request, bando_id,
                        domanda_bando_id, azione='chiudi'):
    """
    in base alla azione viene chiusa la domanda o riaperta
    se la domanda va protocollata se viene riaperta produce rettifica di protocollo
    """
    dipendente = get_object_or_404(Dipendente, matricola=request.user.matricola)
    bando = _get_bando_queryset(bando_id).first()

    domanda_bando = get_object_or_404(DomandaBando,
                                      pk=domanda_bando_id,
                                      dipendente=dipendente,
                                      is_active=True)
    # la rettifica è identica sia con protocollo che senza
    if azione == 'riapri':
        # creazione rettifica
        rettifica = RettificaDomandaBando.objects.create(
                                                    domanda_bando=domanda_bando,
                                                    data_chiusura=domanda_bando.data_chiusura,
                                                    numero_protocollo=domanda_bando.numero_protocollo,
                                                    data_protocollazione=domanda_bando.data_protocollazione,
                                                        )
        # eventuale protocollo e data protocollo vengono sovrascritti solo ad ulteriore chiusura
        # se già protocollato e rettificato vale sempre quello già protocollato
        domanda_bando.data_chiusura = None
        domanda_bando.save()
        page_url = reverse('domande_peo:dashboard_domanda', args=[bando.pk,])
        return HttpResponseRedirect(page_url)

    # check se protocollazione richiesta e se la domanda non è stata già chiusa
    if azione == 'chiudi' and not domanda_bando.data_chiusura:
        if bando.protocollo_required:
            peo_dict = {'wsdl_url' : settings.PROT_URL,
                        'username' : settings.PROT_LOGIN,
                        'password' : settings.PROT_PASSW,
                        'aoo': settings.PROT_AOO,
                        'template_xml_flusso': bando.protocollo_template,

                        'oggetto':'{} - {}'.format(bando, dipendente),
                         # Variabili
                        'matricola_dipendente': dipendente.matricola,
                        'denominazione_persona': ' '.join((dipendente.nome,
                                                           dipendente.cognome,)),

                        # attributi creazione protocollo
                        'id_titolario': bando.protocollo_cod_titolario, # settings.PROTOCOLLO_TITOLARIO_DEFAULT,
                        'fascicolo_numero': bando.protocollo_fascicolo_numero, # settings.PROTOCOLLO_FASCICOLO_DEFAULT,
                        'fascicolo_anno': timezone.localtime().year}

            protclass = __import__(settings.CLASSE_PROTOCOLLO, globals(), locals(), ['*'])
            wsclient = protclass.Protocollo(**peo_dict)

            docPrinc = BytesIO()
            docPrinc.write(download_domanda_pdf(request, bando_id, domanda_bando_id).content)
            docPrinc.seek(0)
            wsclient.aggiungi_docPrinc(docPrinc,
                                       nome_doc="domanda_{}_{}.pdf".format(dipendente.matricola,
                                                                           bando.pk),
                                       tipo_doc='{} - {}'.format(bando.pk, dipendente.matricola))

            for modulo in domanda_bando.modulodomandabando_set.all():
                # aggiungi come allegati solo i moduli che hanno allegati
                # if not modulo.get_allegati(): continue
                if not get_allegati(modulo): continue
                allegato = BytesIO()
                allegato.write(download_modulo_inserito_pdf(request, bando_id, modulo.pk).content)
                allegato.seek(0)
                wsclient.aggiungi_allegato(nome="domanda_{}_{}-{}.pdf".format(dipendente,
                                                                              bando.pk,
                                                                              modulo.pk),
                                           descrizione='{} - {}'.format(modulo.descrizione_indicatore.id_code,
                                                                        modulo.get_identificativo_veloce()),
                                           fopen=allegato)
            # print(wsclient.is_valid())
            if settings.DEBUG: print(wsclient.render_dataXML())
            prot_resp = wsclient.protocolla()
            domanda_bando.numero_protocollo = wsclient.numero
            domanda_bando.data_protocollazione = timezone.localtime()
            # se non torna un numero di protocollo emerge l'eccezione
            assert wsclient.numero

        # chiusura in locale
        domanda_bando.data_chiusura = timezone.localtime()
        domanda_bando.save()

        # invio email di notifica
        if bando.email_avvenuto_completamento and request.user.email:
             smd = {'url': settings.URL,
                    'domanda_url': reverse('domande_peo:riepilogo_domanda',
                                           args=[bando.pk, domanda_bando.pk]),
                    'bando': bando,
                    'dipendente': dipendente}
             send_mail(gestione_peo.settings.COMPLETE_EMAIL_SUBJECT.format(bando),
                       gestione_peo.settings.COMPLETE_EMAIL_BODY.format(**smd),
                       gestione_peo.settings.COMPLETE_EMAIL_SENDER,
                       [request.user.email,],
                       fail_silently=False,
                       auth_user=None,
                       auth_password=None,
                       connection=None,
                       html_message=None)
    domanda_bando.mark_as_modified()

    _breadcrumbs.add_url(('#', 'Chiusura Domanda'))
    d = { 'bando': domanda_bando.bando,
          'domanda_peo': domanda_bando,
          'dipendente': dipendente,
          'MEDIA_URL': settings.MEDIA_URL }
    return render(request, 'chiusura_domanda.html', d)
