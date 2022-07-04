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

import logging
import gestione_peo.settings
import json
import magic
import shutil


logger = logging.getLogger(__name__)
_breadcrumbs = BreadCrumbs()

# Ci dice se un utente è staff o fa parte di una commissione
# attiva e in corso per il bando passato come argomento
# Questo serve per dare accesso agli allegati delle domande
def _user_is_staff_or_in_commission(user, bando):
    if not user: return False
    if user.is_staff: return True
    if not bando: return False
    commissioni = CommissioneGiudicatrice.objects.filter(bando=bando,
                                                         is_active=True)
    for commissione in commissioni:
        if not commissione.is_in_corso(): continue
        commissione_utente = CommissioneGiudicatriceUsers.objects.filter(commissione=commissione,
                                                                         user=user,
                                                                         is_active=True).first()
        if not commissione_utente: continue
        if not commissione_utente.ha_accettato_clausole(): continue
        return True
    return False

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
    domanda_bando = DomandaBando.objects.filter(bando=bando,
                                                dipendente=dipendente)

    # se non c'è alcuna domanda, la creo
    # se la domanda c'è ma is_active==False, ritorno un messaggio di errore
    # altrimenti si prosegue con la domanda attualmente presente
    if domanda_bando:
        domanda_bando = domanda_bando.last()
    elif not domanda_bando:
        url = reverse('domande_peo:scelta_titolo_da_aggiungere',
                      args=[bando.slug])
        return HttpResponseRedirect(url)

    if not domanda_bando.modulodomandabando_set.all() and not domanda_bando.bando.indicatore_con_anzianita():
        url = reverse('domande_peo:scelta_titolo_da_aggiungere',
                      args=[bando.slug])
        return HttpResponseRedirect(url)

    if not domanda_bando.is_active:
        return render(request, 'custom_message.html',
                      {'avviso': ("La tua Domanda è stata sospesa. Per avere "
                                  "informazioni contatta l' Area Risorse Umane.")})

    page_title = 'Partecipazione Bando/Avviso {}'.format(bando.nome)
    page_url = reverse('domande_peo:dashboard_domanda',
                       args=[bando.slug])
    _breadcrumbs.reset()
    _breadcrumbs.add_url((page_url, page_title))

    context = {'page_title': page_title,
               'breadcrumbs': _breadcrumbs,
               'bando': bando,
               'dipendente': dipendente,
               'domanda_bando': domanda_bando}
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
    domanda_bando = DomandaBando.objects.filter(bando=bando,
                                                dipendente=dipendente)

    # se non c'è alcuna domanda, la creo
    # se la domanda c'è ma is_active==False, ritorno un messaggio di errore
    # altrimenti si prosegue con la domanda attualmente presente
    if domanda_bando:
        domanda_bando = domanda_bando.last()
    elif not domanda_bando:
        domanda_bando = DomandaBando.objects.create(bando=bando,
                                                    dipendente=dipendente,
                                                    modified=timezone.localtime(),
                                                    livello=dipendente.livello,
                                                    data_presa_servizio=dipendente.get_data_presa_servizio_csa(),
                                                    data_ultima_progressione=dipendente.get_data_progressione())
    if not domanda_bando.is_active:
        return render(request, 'custom_message.html',
                      {'avviso': ("La tua Domanda è stata sospesa. Per avere "
                                  "informazioni contatta l' Area Risorse Umane.")})

    dashboard_domanda_title = 'Partecipazione Bando/Avviso {}'.format(bando.nome)
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
        'domanda_bando': domanda_bando,
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
    bando = _get_bando_queryset(bando_id).first()
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
    bando = _get_bando_queryset(bando_id).first()
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
    bando = _get_bando_queryset(bando_id).first()
    descrizione_indicatore = modulo_domanda_bando.descrizione_indicatore
    json_dict = json.loads(modulo_domanda_bando.modulo_compilato)
    data = get_as_dict(json_dict, allegati=False)
    allegati = get_allegati_dict(modulo_domanda_bando)
    form = SavedFormContent.compiled_form_readonly(modulo_domanda_bando.compiled_form(remove_filefields=allegati))
    # form con i soli campi File da dare in pasto al tag della firma digitale
    form_allegati = descrizione_indicatore.get_form(remove_datafields=True)
    d = {
         'allegati': allegati,
         'form': form,
         'form_allegati': form_allegati,
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
                                      bando=bando,
                                      dipendente=dipendente,
                                      is_active=True)
    descrizione_indicatore = get_object_or_404(DescrizioneIndicatore,
                                               pk=descrizione_indicatore_id)

    # From gestione_peo/templatetags/indicatori_ponderati_tags
    # if not descrizione_indicatore.is_available_for_cat_role(dipendente.livello.posizione_economica,
    if not descrizione_indicatore.is_available_for_cat_role(domanda_bando.livello.posizione_economica,
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
                                           domanda_bando=domanda_bando)

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
        return_url = reverse('domande_peo:dashboard_domanda', args=[bando.pk,])
        result = aggiungi_titolo_form(request=request,
                                      bando=bando,
                                      descrizione_indicatore=descrizione_indicatore,
                                      domanda_bando=domanda_bando,
                                      dipendente=dipendente,
                                      return_url=return_url,
                                      log=False)
        if result:
            if isinstance(result, HttpResponseRedirect): return result
            for k in result:
                d[k] = result[k]

    d['labeled_errors'] = get_labeled_errors(d['form'])

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
                            domanda_bando__is_active=True,
                            domanda_bando__dipendente=dipendente)

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
        return_url = reverse('domande_peo:modifica_titolo',
                            args=[bando.pk,modulo_compilato_id])
        result = modifica_titolo_form(request=request,
                                      bando=bando,
                                      descrizione_indicatore=descrizione_indicatore,
                                      mdb=mdb,
                                      allegati=allegati,
                                      path_allegati=path_allegati,
                                      return_url=return_url,
                                      log=False)
        if result:
            if isinstance(result, HttpResponseRedirect): return result
            for k in result:
                d[k] = result[k]

    d['labeled_errors'] = get_labeled_errors(d['form'])

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
    return_url = reverse('domande_peo:dashboard_domanda', args=[bando.pk,])
    return cancella_titolo_from_domanda(request,
                                        bando,
                                        dipendente,
                                        mdb,
                                        return_url,
                                        mark_domanda_as_modified=True,
                                        log=False)

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

    return_url = reverse('domande_peo:modifica_titolo', args=[bando.id, mdb.id])
    return elimina_allegato_from_mdb(request,
                                     bando,
                                     dipendente,
                                     mdb,
                                     allegato,
                                     return_url,
                                     log=False)

@login_required
# @abilitato_a_partecipare
def download_allegato(request, bando_id, modulo_compilato_id, allegato):
    """
        Download del file allegato, dopo aver superato i check di proprietà
    """
    bando = _get_bando_queryset(bando_id).first()

    # se scarica un utente staff o la commissione può accedervi
    if _user_is_staff_or_in_commission(request.user, bando):
        mdb = get_object_or_404(ModuloDomandaBando,
                                pk=modulo_compilato_id)
        dipendente = get_object_or_404(Dipendente,
                                       matricola=mdb.domanda_bando.dipendente.matricola)
    # altrimenti solo se l'utente è il proprietario e la domanda è attiva
    else:
        dipendente = get_object_or_404(Dipendente,
                                       matricola=request.user.matricola)
        mdb = get_object_or_404(ModuloDomandaBando,
                                pk=modulo_compilato_id,
                                domanda_bando__is_active=True,
                                domanda_bando__dipendente=dipendente)

    return download_allegato_from_mdb(bando,
                                      mdb,
                                      dipendente,
                                      allegato)

@login_required
def riepilogo_domanda(request, bando_id, domanda_bando_id, pdf=None):
    """
        Esegue l'output in pdf
    """
    bando = _get_bando_queryset(bando_id).first()
    # se scarica un utente staff o un membro della commissione può accedervi
    if _user_is_staff_or_in_commission(request.user, bando):
        domanda_bando = get_object_or_404(DomandaBando,
                                          pk=domanda_bando_id,
                                          bando=bando)
    # altrimenti solo se l'utente è il proprietario e la domanda è attiva
    else:
        dipendente = get_object_or_404(Dipendente,
                                       matricola=request.user.matricola)
        domanda_bando = get_object_or_404(DomandaBando,
                                          pk=domanda_bando_id,
                                          bando=bando,
                                          dipendente=dipendente,
                                          is_active=True)
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
        'domanda_bando': domanda_bando,
        'MEDIA_URL': settings.MEDIA_URL}
    if pdf:
        return render(request, 'riepilogo_domanda_pdf.html', d)
    elif request.user!=domanda_bando.dipendente.utente:
        return render(request, 'riepilogo_domanda_admin.html', d)
    return render(request, 'riepilogo_domanda.html', d)

@login_required
def download_modulo_inserito_pdf(request, bando_id, modulo_compilato_id):
    """
        Esegue l'output in pdf
        riutilizzando le view precedenti evitiamo di rifare gli stessi controlli
        ricicliamo query e decoratori
    """
    bando = _get_bando_queryset(bando_id).first()
    # se scarica un utente staff o un membro della commissione può accedervi
    if _user_is_staff_or_in_commission(request.user, bando):
        mdb = get_object_or_404(ModuloDomandaBando,
                                pk=modulo_compilato_id,
                                domanda_bando__bando=bando)
        dipendente = mdb.domanda_bando.dipendente
    # altrimenti solo se l'utente è il proprietario e la domanda è attiva
    else:
        dipendente = get_object_or_404(Dipendente,
                                       matricola=request.user.matricola)
        mdb = get_object_or_404(ModuloDomandaBando,
                                pk=modulo_compilato_id,
                                domanda_bando__dipendente=dipendente,
                                domanda_bando__bando=bando)


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
        dump_domanda = []
        mdbs = ModuloDomandaBando.objects.filter(domanda_bando=domanda_bando)
        for mdb in mdbs:
            inner_list = []
            inner_list.append(("id", mdb.pk))
            inner_list.append(("created", mdb.created.__str__()))
            inner_list.append(("modified", mdb.modified.__str__()))
            inner_list.append(("modulo_compilato", mdb.modulo_compilato))
            inner_list.append(("descrizione_indicatore_id", mdb.descrizione_indicatore_id))
            dump_domanda.append(inner_list)
            dump_json = json.dumps(dump_domanda, indent=2)

        rettifica = RettificaDomandaBando.objects.create(domanda_bando=domanda_bando,
                                                         data_chiusura=domanda_bando.data_chiusura,
                                                         numero_protocollo=domanda_bando.numero_protocollo,
                                                         data_protocollazione=domanda_bando.data_protocollazione,
                                                         dump=dump_json)
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

            logger.info('Protocollazione Domanda {}'.format(domanda_bando))
            docPrinc = BytesIO()
            docPrinc.write(download_domanda_pdf(request, bando_id, domanda_bando_id).content)
            docPrinc.seek(0)
            wsclient.aggiungi_docPrinc(docPrinc,
                                       nome_doc="domanda_{}_{}.pdf".format(dipendente.matricola,
                                                                           bando.pk),
                                       tipo_doc='{} - {}'.format(bando.pk, dipendente.matricola))

            # allegati disabilitati
            # for modulo in domanda_bando.modulodomandabando_set.all():
                # if not get_allegati(modulo): continue
                # allegato = BytesIO()
                # logger.info('Protocollazione Domanda {} - allegato {}'.format(domanda_bando,
                                                                              # modulo.pk))
                # allegato.write(download_modulo_inserito_pdf(request, bando_id, modulo.pk).content)
                # allegato.seek(0)
                # wsclient.aggiungi_allegato(nome="domanda_{}_{}-{}.pdf".format(dipendente,
                                                                              # bando.pk,
                                                                              # modulo.pk),
                                           # descrizione='{} - {}'.format(modulo.descrizione_indicatore.id_code,
                                                                        # modulo.get_identificativo_veloce()),
                                           # fopen=allegato)
            # print(wsclient.is_valid())
            logger.debug(wsclient.render_dataXML())
            prot_resp = wsclient.protocolla()
            domanda_bando.numero_protocollo = wsclient.numero
            logger.info('Avvenuta Protocollazione Domanda {} numero: {}'.format(domanda_bando,
                                                                                domanda_bando.numero_protocollo))
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
          'domanda_bando': domanda_bando,
          'dipendente': dipendente,
          'MEDIA_URL': settings.MEDIA_URL }
    return render(request, 'chiusura_domanda.html', d)
