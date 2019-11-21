import json

from django_auto_serializer.auto_serializer import ImportableSerializedInstance

from django.conf import settings
from django.contrib import auth, messages
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE
from django.contrib.auth.decorators import (login_required,
                                            user_passes_test)
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q

from django.http import Http404
from django.http.response import HttpResponseRedirect
from django.shortcuts import (get_object_or_404, render,
                              render_to_response, redirect)
from django.urls import reverse
from django.utils import timezone
from django.utils.http import is_safe_url
from django.utils.translation import gettext as _

from django_form_builder.utils import (get_allegati,
                                       get_allegati_dict,
                                       get_as_dict,
                                       get_labeled_errors,
                                       get_POST_as_json,
                                       set_as_dict)

from domande_peo.decorators import abilitato_a_partecipare
from domande_peo.forms import AccettazioneClausoleForm
from domande_peo.models import DomandaBando, ModuloDomandaBando
from domande_peo.utils import *
from gestione_risorse_umane.models import Dipendente
from gestione_risorse_umane.decorators import (user_in_commission,
                                               user_can_manage_commission)
from unical_accounts.models import User
from unical_template.breadcrumbs import BreadCrumbs

from .decorators import _get_bando_queryset, check_accessibilita_bando, check_termini_domande
from .forms import *
from .models import *
from .utils import *

_breadcrumbs = BreadCrumbs()

@login_required
def bandi_peo(request):
    """"""

    dipendente = request.user.dipendente_set.filter(matricola=request.user.matricola).first()

    if dipendente.utente.is_staff:
        bandi_lista = Bando.objects.filter(Q(pubblicato=True) | Q(collaudo=True))
        bandi_attivi = dipendente.idoneita_peo_staff()
    else:
        bandi_lista = Bando.objects.filter(pubblicato=True)
        bandi_attivi = dipendente.idoneita_peo_attivata()

    if bandi_lista:
        bandi_lista = bandi_lista.order_by('-data_inizio')

    excluded_pk=[]
    for bando in bandi_attivi:
        if not bando.is_in_corso():
            excluded_pk.append(bando.pk)
    bandi_attivi = bandi_lista.exclude(pk__in=excluded_pk)

    page_title = 'Bandi PEO'
    page_url = reverse('gestione_peo:bandi_peo')
    _breadcrumbs.reset()
    _breadcrumbs.add_url((page_url, page_title))

    context = {
        "page_title": page_title,
        "breadcrumbs": _breadcrumbs,
        "bandi": bandi_attivi,
        "bandi_lista": bandi_lista,
        "dipendente": dipendente,

    }
    return render(request, "bandi_peo.html",context=context)

@login_required
@check_accessibilita_bando
def dettaglio_bando_peo(request, bando_id):
    """"""
    #bando_peo = get_object_or_404(Bando, pk=bando_id)
    bando = _get_bando_queryset(bando_id).first()

    dipendente = Dipendente.objects.filter(matricola=request.user.matricola).first()
    #categorie_titoli = CategoriaTitolo.objects.filter(Bando=Bando_id).order_by('ordinamento')

    # Se non c'è un bando pubblicato e l'utente non ha privilegi di staff
    # la risorsa non è accessibile
    #if not (bando.pubblicato or dipendente.utente.is_staff):
    #    url = reverse('risorse_umane:dashboard')
    #    return HttpResponseRedirect(url)

    page_title = 'Descrizione parametri di Partecipazione al Bando {}'.format(bando.nome)
    url_bandi_peo = reverse('gestione_peo:bandi_peo')
    page_url = reverse('gestione_peo:dettaglio_bando_peo',
                      args=[bando.slug])
    _breadcrumbs.reset()
    _breadcrumbs.add_url((url_bandi_peo,'Bandi PEO'))
    _breadcrumbs.add_url((page_url, page_title))
    d = {
         "page_title": page_title,
         "breadcrumbs": _breadcrumbs,
         "bando": bando,
         "dipendente": dipendente
        #"categorie_titoli": categorie_titoli,
    }
    return render(request, "dettaglio_bando_peo.html",context=d)


@user_passes_test(lambda u:u.is_staff)
def import_file(request):
    file_to_import = request.FILES.get('file_to_import')
    # content here
    url = reverse('admin:gestione_peo_bando_changelist')
    if not file_to_import:
        return HttpResponseRedirect(url)
    if not file_to_import:
        # scrivi un messaggio di errore
        pass
    jcont = json.loads(request.FILES['file_to_import'].read().decode(settings.DEFAULT_CHARSET))
    isi = ImportableSerializedInstance(jcont)
    isi.save()
    return HttpResponseRedirect(url)

@login_required
@abilitato_a_partecipare
def download_avviso(request, bando_id, avviso_id):
    bando = get_object_or_404(Bando, slug=bando_id)
    avviso = get_object_or_404(AvvisoBando,
                               bando=bando,
                               pk=avviso_id)
    allegato = avviso.allegato
    result = download_file(settings.MEDIA_ROOT, allegato)

    if result is None: raise Http404
    return result

@login_required
def commissioni(request):
    """"""

    commissioni = get_commissioni_attive(request.user)

    page_title = 'Commissioni'
    page_url = reverse('gestione_peo:commissioni')
    _breadcrumbs.reset()
    _breadcrumbs.add_url((page_url, page_title))

    context = {
        "page_title": page_title,
        "breadcrumbs": _breadcrumbs,
        "commissioni": commissioni,
    }
    return render(request, "commissioni.html",context=context)

@login_required
@user_in_commission
def commissione_dettaglio(request, commissione_id,
                          commissione, commissione_user):
    """
    commissione argument comes from decorator @user_in_commission
    commissione_user argument comes from decorator @user_in_commission
    """
    commissioni = get_commissioni_attive(request.user)
    commissioni_in_corso = get_commissioni_in_corso(request.user, commissioni)
    clausole = commissione.get_clausole_attive()

    if request.method == 'POST':
        form = AccettazioneClausoleForm(request.POST)
        if form.is_valid():
            conferma = request.POST["accettazione"]
            if conferma:
                commissione_user.clausole_accettate = True
                commissione_user.save(update_fields = ['clausole_accettate',
                                                       'modified'])
                messages.add_message(request, messages.SUCCESS,
                                     _("Clausole accettate con successo"))
        else:
            messages.add_message(request, messages.ERROR,
                                 _("E' necessario accettare le clausole"))
        return redirect('gestione_peo:dettaglio_commissione',
                        commissione_id=commissione.pk)
    else:
        form = AccettazioneClausoleForm()

    page_title = commissione
    url_commissioni = reverse('gestione_peo:commissioni')
    page_url = reverse('gestione_peo:dettaglio_commissione',
                      args=[commissione.pk])
    _breadcrumbs.reset()
    _breadcrumbs.add_url((url_commissioni,'Commissioni'))
    _breadcrumbs.add_url((page_url, page_title))

    d = {
        'clausole': clausole,
        'commissione': commissione,
        'commissione_user': commissione_user,
        'commissioni': commissioni,
        'commissioni_in_corso': commissioni_in_corso,
        'form': form,
        'page_title': page_title,
        'breadcrumbs': _breadcrumbs,
    }
    return render(request, "commissione_dettaglio.html", context=d)

@login_required
@user_in_commission
@user_can_manage_commission
def commissione_manage(request, commissione_id,
                       commissione, commissione_user):
    """
    commissione argument comes from decorator @user_in_commission
    commissione_user argument comes from decorator @user_in_commission
    """
    commissioni_utente = CommissioneGiudicatriceUsers.objects.filter(user=request.user,
                                                                     user__is_active=True)
    commissioni = get_commissioni_attive(request.user)
    commissioni_in_corso = get_commissioni_in_corso(request.user, commissioni)

    bando = commissione.bando
    search = request.GET.get('search')
    domande_bando = DomandaBando.objects.filter(bando=bando,
                                                is_active=True)
    if search:
        domande_bando = domande_bando.filter(Q(dipendente__matricola__icontains=search) |
                                             Q(dipendente__nome__icontains=search) |
                                             Q(dipendente__cognome__icontains=search) |
                                             Q(numero_protocollo=search))
    url_commissioni = reverse('gestione_peo:commissioni')
    url_commissione = reverse('gestione_peo:dettaglio_commissione',
                              args=[commissione.pk])
    page_url = reverse('gestione_peo:manage_commissione',
                       args=[commissione.pk])
    _breadcrumbs.reset()
    _breadcrumbs.add_url((url_commissioni,'Commissioni'))
    _breadcrumbs.add_url((url_commissione,commissione))
    _breadcrumbs.add_url((page_url, 'Gestione domande'))
    d = {
        'breadcrumbs': _breadcrumbs,
        'commissione': commissione,
        'commissioni': commissioni,
        'commissioni_in_corso': commissioni_in_corso,
        'domande': domande_bando,
        'search': search,
    }
    return render(request, "commissione_manage.html", context=d)

@login_required
@user_in_commission
@user_can_manage_commission
def commissione_download_allegato(request, commissione_id, domanda_id,
                                  modulo_id, allegato,
                                  commissione, commissione_user):
    """
        Download del file allegato, dopo aver superato i check di proprietà
    """
    bando = commissione.bando
    domanda_peo = get_object_or_404(DomandaBando,
                                    pk=domanda_id,
                                    bando=bando)
    mdb = get_object_or_404(ModuloDomandaBando,
                            pk=modulo_id,
                            domanda_bando=domanda_peo)
    dipendente = domanda_peo.dipendente

    return download_allegato_from_mdb(bando,
                                      mdb,
                                      dipendente,
                                      allegato)

@login_required
@user_in_commission
@user_can_manage_commission
def commissione_domanda_manage(request, commissione_id, domanda_id,
                               commissione, commissione_user):
    bando = commissione.bando
    # recupero la domanda peo del dipendente
    domanda_peo = get_object_or_404(DomandaBando,
                                    pk=domanda_id,
                                    bando=bando)
    dipendente = domanda_peo.dipendente

    url_commissioni = reverse('gestione_peo:commissioni')
    url_commissione = reverse('gestione_peo:dettaglio_commissione',
                              args=[commissione.pk])
    url_manage = reverse('gestione_peo:manage_commissione',
                         args=[commissione.pk])
    page_url = reverse('gestione_peo:commissione_domanda_manage',
                       args=[commissione.pk, domanda_id])
    page_title = 'Domanda {}'.format(domanda_peo)
    _breadcrumbs.reset()
    _breadcrumbs.add_url((url_commissioni,'Commissioni'))
    _breadcrumbs.add_url((url_commissione,commissione))
    _breadcrumbs.add_url((url_manage, 'Gestione domande'))
    _breadcrumbs.add_url((page_url, page_title))

    commissioni = get_commissioni_attive(request.user)
    commissioni_in_corso = get_commissioni_in_corso(request.user, commissioni)

    context = {'bando': bando,
               'breadcrumbs': _breadcrumbs,
               'commissione': commissione,
               'commissioni': commissioni,
               'commissioni_in_corso': commissioni_in_corso,
               'dipendente': dipendente,
               'domanda_peo': domanda_peo,
               'page_title': page_title
               }

    if request.method == 'POST':
        # azione di calcolo punteggio
        if request.POST.get('calcola_punteggio'):
            punteggio = domanda_peo.calcolo_punteggio_domanda(save=True)
            msg = ("Punteggio calcolato con successo "
                   "({}) per la domanda {}").format(punteggio,
                                                    domanda_peo)
        # mostra il messaggio
        messages.add_message(request, messages.SUCCESS, msg)
        # Logging di ogni azione compiuta sulla domanda dalla commissione
        LogEntry.objects.log_action(user_id = request.user.pk,
                                    content_type_id = ContentType.objects.get_for_model(domanda_peo).pk,
                                    object_id       = domanda_peo.pk,
                                    object_repr     = domanda_peo.__str__(),
                                    action_flag     = CHANGE,
                                    change_message  = msg)
        # Per evitare che al refresh
        # possa essere effettuata una nuova richiesta POST
        url = reverse('gestione_peo:commissione_domanda_manage',
                      args=[commissione_id, domanda_id])
        return HttpResponseRedirect(url)
    return render(request, "commissione_dashboard_domanda.html", context=context)

@login_required
@user_in_commission
@user_can_manage_commission
def commissione_disabilita_domanda(request, commissione_id, domanda_id,
                                   commissione, commissione_user):
    bando = commissione.bando
    # recupero la domanda peo del dipendente
    domanda_bando = get_object_or_404(DomandaBando,
                                      pk=domanda_id,
                                      bando=bando)
    domanda_bando.is_active = False
    domanda_bando.save(update_fields=['is_active',])
    msg = ("Domanda {} disabilitata correttamente").format(domanda_bando)
    LogEntry.objects.log_action(user_id = request.user.pk,
                                content_type_id = ContentType.objects.get_for_model(domanda_bando).pk,
                                object_id       = domanda_bando.pk,
                                object_repr     = domanda_bando.__str__(),
                                action_flag     = CHANGE,
                                change_message  = msg)
    messages.add_message(request, messages.SUCCESS, msg)
    url = reverse('gestione_peo:commissione_domanda_manage',
                  args=[commissione_id, domanda_id])
    return HttpResponseRedirect(url)

@login_required
@user_in_commission
@user_can_manage_commission
def commissione_abilita_domanda(request, commissione_id, domanda_id,
                                commissione, commissione_user):
    bando = commissione.bando
    # recupero la domanda peo del dipendente
    domanda_bando = get_object_or_404(DomandaBando,
                                      pk=domanda_id,
                                      bando=bando)
    domanda_bando.is_active = True
    domanda_bando.save(update_fields=['is_active',])
    msg = ("Domanda {} abilitata correttamente").format(domanda_bando)
    LogEntry.objects.log_action(user_id = request.user.pk,
                                content_type_id = ContentType.objects.get_for_model(domanda_bando).pk,
                                object_id       = domanda_bando.pk,
                                object_repr     = domanda_bando.__str__(),
                                action_flag     = CHANGE,
                                change_message  = msg)
    messages.add_message(request, messages.SUCCESS, msg)
    url = reverse('gestione_peo:commissione_domanda_manage',
                  args=[commissione_id, domanda_id])
    return HttpResponseRedirect(url)

@login_required
@user_in_commission
@user_can_manage_commission
def commissione_domanda_scegli_titolo(request, commissione_id, domanda_id,
                                      commissione, commissione_user):
    bando = commissione.bando
    # recupero la domanda peo del dipendente
    domanda_peo = get_object_or_404(DomandaBando,
                                    pk=domanda_id,
                                    bando=bando)
    dipendente = domanda_peo.dipendente

    indicatori_ponderati = bando.indicatoreponderato_set.all().order_by('id_code')

    # if not domanda_peo.is_active:
        # return render(request, 'custom_message.html',
                      # {'avviso': ("La tua Domanda è stata sospesa. Per avere "
                                  # "informazioni contatta l' Area Risorse Umane.")})
    # dashboard_domanda_title = 'Partecipazione Bando {}'.format(bando.nome)
    # dashboard_domanda_url = reverse('domande_peo:dashboard_domanda',
                                    # args=[bando.slug])

    url_commissioni = reverse('gestione_peo:commissioni')
    url_commissione = reverse('gestione_peo:dettaglio_commissione',
                              args=[commissione.pk])
    url_manage = reverse('gestione_peo:manage_commissione',
                         args=[commissione.pk])
    url_domanda = reverse('gestione_peo:commissione_domanda_manage',
                          args=[commissione.pk, domanda_id])
    page_url = reverse('gestione_peo:commissione_domanda_scegli_titolo',
                       args=[commissione.pk, domanda_id])
    page_title = 'Selezione Modulo di Inserimento'

    _breadcrumbs.reset()
    _breadcrumbs.add_url((url_commissioni,'Commissioni'))
    _breadcrumbs.add_url((url_commissione,commissione))
    _breadcrumbs.add_url((url_manage, 'Gestione domande'))
    _breadcrumbs.add_url((url_domanda, 'Domanda {}'.format(domanda_peo)))
    _breadcrumbs.add_url((page_url, page_title))

    commissioni = get_commissioni_attive(request.user)
    commissioni_in_corso = get_commissioni_in_corso(request.user, commissioni)

    context = {
        'commissione': commissione,
        'commissioni': commissioni,
        'commissioni_in_corso': commissioni_in_corso,
        'page_title': page_title,
        'breadcrumbs': _breadcrumbs,
        'bando': bando,
        'dipendente': dipendente,
        'domanda_peo': domanda_peo,
        'indicatori_ponderati': indicatori_ponderati,
    }
    return render(request, "commissione_scelta_titolo_da_aggiungere.html",context=context)

@login_required
@user_in_commission
@user_can_manage_commission
def commissione_domanda_aggiungi_titolo(request, commissione_id,
                                        domanda_id, descrizione_indicatore_id,
                                        commissione, commissione_user ):
    """
        Costruisce form da PeodynamicForm
        li valida e salva i dati all'occorrenza
    """
    bando = commissione.bando
    # recupero la domanda peo del dipendente
    domanda_bando = get_object_or_404(DomandaBando,
                                      pk=domanda_id,
                                      bando=bando)
    dipendente = domanda_bando.dipendente
    descrizione_indicatore = get_object_or_404(DescrizioneIndicatore,
                                               pk = descrizione_indicatore_id)

    # From gestione_peo/templatetags/indicatori_ponderati_tags
    if not descrizione_indicatore.is_available_for_cat_role(dipendente.livello.posizione_economica,
                                                            dipendente.ruolo):
        return render(request, 'custom_message.html',
                      {'avviso': ("La posizione o il ruolo del dipendente"
                                  " risultano disabilitati"
                                  " all'accesso a questo modulo.")})

    # From domande_peo/templatetags/domande_peo_tags
    # if descrizione_indicatore.limite_inserimenti:
        # mdb_presenti = domanda_bando.num_mdb_tipo_inseriti(descrizione_indicatore)
        # if mdb_presenti == descrizione_indicatore.numero_inserimenti:
            # return render(request, 'custom_message.html',
                          # {'avviso': ("Hai raggiunto il numero di inserimenti"
                                      # " consentiti per questo modulo")})

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
    url_commissioni = reverse('gestione_peo:commissioni')
    url_commissione = reverse('gestione_peo:dettaglio_commissione',
                              args=[commissione.pk])
    url_manage = reverse('gestione_peo:manage_commissione',
                         args=[commissione.pk])
    url_domanda = reverse('gestione_peo:commissione_domanda_manage',
                          args=[commissione.pk, domanda_id])
    url_scelta_titolo = reverse('gestione_peo:commissione_domanda_scegli_titolo',
                                args=[commissione.pk, domanda_id])
    page_url = reverse('gestione_peo:commissione_domanda_aggiungi_titolo',
                       args=[commissione.pk, domanda_id, descrizione_indicatore_id])
    page_title = 'Selezione Modulo di Inserimento'

    _breadcrumbs.reset()
    _breadcrumbs.add_url((url_commissioni,'Commissioni'))
    _breadcrumbs.add_url((url_commissione,commissione))
    _breadcrumbs.add_url((url_manage, 'Gestione domande'))
    _breadcrumbs.add_url((url_domanda, 'Domanda {}'.format(domanda_bando)))
    _breadcrumbs.add_url((url_scelta_titolo, 'Scegli titolo'))
    _breadcrumbs.add_url((page_url, page_title))

    commissioni = get_commissioni_attive(request.user)
    commissioni_in_corso = get_commissioni_in_corso(request.user, commissioni)

    d = {'commissione': commissione,
         'commissioni': commissioni,
         'commissioni_in_corso': commissioni_in_corso,
         'domanda_bando': domanda_bando,
         'page_title': page_title,
         'breadcrumbs': _breadcrumbs,
         'form': form,
         'bando':bando,
         'dipendente': dipendente,
         'descrizione_indicatore': descrizione_indicatore}

    if request.method == 'POST':
        return_url = reverse('gestione_peo:commissione_domanda_manage',
                             args=[commissione.pk, domanda_bando.pk,])
        result = aggiungi_titolo_form(request=request,
                                      bando=bando,
                                      descrizione_indicatore=descrizione_indicatore,
                                      domanda_bando=domanda_bando,
                                      dipendente=dipendente,
                                      return_url=return_url,
                                      log=True)
        if result:
            if isinstance(result, HttpResponseRedirect): return result
            for k in result:
                d[k] = result[k]

    d['labeled_errors'] = get_labeled_errors(form)
    return render(request, 'commissione_modulo_form.html', d)

@login_required
@user_in_commission
@user_can_manage_commission
def commissione_modulo_domanda_modifica(request, commissione_id, domanda_id,
                                        modulo_id, commissione, commissione_user):
    """
        Costruisce form da PeodynamicForm
        li valida e salva i dati all'occorrenza

        remove_filefields prende il valore che concorre a selezionare il template readonly
        usato per readonly=pdf, inoltre rimuove i filefields dal form
    """
    bando = commissione.bando
    domanda_bando = get_object_or_404(DomandaBando,
                                      pk=domanda_id,
                                      bando=bando)
    dipendente = domanda_bando.dipendente
    mdb = get_object_or_404(ModuloDomandaBando,
                            pk=modulo_id,
                            domanda_bando__dipendente=dipendente)

    descrizione_indicatore = mdb.descrizione_indicatore
    allegati = get_allegati_dict(mdb)
    form = mdb.compiled_form(remove_filefields=allegati)
    form_allegati = descrizione_indicatore.get_form(remove_datafields=True)
    dashboard_domanda_title = 'Partecipazione Bando {}'.format(bando.nome)
    dashboard_domanda_url = reverse('domande_peo:dashboard_domanda',
                                    args=[bando.slug])

    path_allegati = get_path_allegato(dipendente.matricola,
                                      bando.slug,
                                      mdb.pk)

    page_title = 'Modifica Inserimento: "({}) {}"'.format(descrizione_indicatore.id_code,
                                                          descrizione_indicatore.nome)
    page_url = reverse('gestione_peo:commissione_modulo_domanda_modifica',
                       args=[commissione_id, domanda_id, modulo_id])
    url_commissioni = reverse('gestione_peo:commissioni')
    url_commissione = reverse('gestione_peo:dettaglio_commissione',
                              args=[commissione.pk])
    url_manage = reverse('gestione_peo:manage_commissione',
                         args=[commissione.pk])
    url_domanda = reverse('gestione_peo:commissione_domanda_manage',
                          args=[commissione.pk, domanda_id])
    _breadcrumbs.reset()
    _breadcrumbs.add_url((url_commissioni,'Commissioni'))
    _breadcrumbs.add_url((url_commissione,commissione))
    _breadcrumbs.add_url((url_manage, 'Gestione domande'))
    _breadcrumbs.add_url((url_domanda, 'Domanda {}'.format(domanda_bando)))
    _breadcrumbs.add_url((page_url, page_title))

    commissioni = get_commissioni_attive(request.user)
    commissioni_in_corso = get_commissioni_in_corso(request.user, commissioni)

    d = {
         'allegati': allegati,
         'bando': bando,
         'breadcrumbs': _breadcrumbs,
         'commissione': commissione,
         'commissioni': commissioni,
         'commissioni_in_corso': commissioni_in_corso,
         'dipendente': dipendente,
         'domanda_peo': domanda_bando,
         'form': form,
         'form_allegati': form_allegati,
         'modulo_domanda_bando': mdb,
         'page_title': page_title,
         'path_allegati': path_allegati,
         }

    if request.method == 'POST':
        if request.POST.get('disable_input'):
            disabilita_abilita = request.POST.get('disabilita_abilita_inserimento')
            motivazione = request.POST.get('motivazione') or mdb.disabilita
            if disabilita_abilita and motivazione:
                mdb.disabilita = not mdb.disabilita
                mdb.motivazione = motivazione
                mdb.save(update_fields=['disabilita', 'motivazione'])
                if mdb.disabilita:
                    msg = ("Inserimento {} disabilitato con successo").format(mdb)
                else:
                    msg = ("Inserimento {} abilitato con successo").format(mdb)
                messages.add_message(request, messages.SUCCESS, msg)
                # Logging di ogni azione compiuta sulla domanda dalla commissione
                LogEntry.objects.log_action(user_id = request.user.pk,
                                            content_type_id = ContentType.objects.get_for_model(domanda_bando).pk,
                                            object_id       = domanda_bando.pk,
                                            object_repr     = domanda_bando.__str__(),
                                            action_flag     = CHANGE,
                                            change_message  = msg)
                # Per evitare che al refresh
                # possa essere effettuata una nuova richiesta POST
                url = reverse('gestione_peo:commissione_domanda_manage',
                              args=[commissione_id, domanda_id])
                return HttpResponseRedirect(url)
            else:
                msg = ("Per disabilitare un inserimento è necessario inserire una motivazione")
                messages.add_message(request, messages.ERROR, msg)
        else:
            if mdb.added_by_user():
                return render(request, 'custom_message.html',
                              {'avviso': ("Impossibile modificare inserimenti creati dal dipendente.")})
            return_url = reverse('gestione_peo:commissione_modulo_domanda_modifica',
                                 args=[commissione_id, domanda_id, modulo_id])
            result = modifica_titolo_form(request=request,
                                          bando=bando,
                                          descrizione_indicatore=descrizione_indicatore,
                                          mdb=mdb,
                                          allegati=allegati,
                                          path_allegati=path_allegati,
                                          return_url=return_url,
                                          log=True)
            if result:
                if isinstance(result, HttpResponseRedirect): return result
                for k in result:
                    d[k] = result[k]

    d['labeled_errors'] = get_labeled_errors(form)
    return render(request, 'commissione_modulo_form_modifica.html', d)

@login_required
@user_in_commission
@user_can_manage_commission
def commissione_elimina_allegato(request, commissione_id, domanda_id,
                                 modulo_id, allegato,
                                 commissione, commissione_user):
    """
        Deve essere chiamato da una dialog con checkbox di conferma
    """
    bando = commissione.bando
    domanda_bando = get_object_or_404(DomandaBando,
                                      pk=domanda_id,
                                      bando=bando)
    dipendente = domanda_bando.dipendente
    mdb = get_object_or_404(ModuloDomandaBando,
                            pk=modulo_id,
                            domanda_bando__dipendente=dipendente)
    if mdb.added_by_user():
        return render(request, 'custom_message.html',
                      {'avviso': ("Impossibile modificare inserimenti creati dal dipendente.")})

    return_url = reverse('gestione_peo:commissione_modulo_domanda_modifica',
                         args=[commissione.pk, domanda_bando.pk, mdb.pk])
    return elimina_allegato_from_mdb(request,
                                     bando,
                                     dipendente,
                                     mdb,
                                     allegato,
                                     return_url,
                                     log=True)

@login_required
@user_in_commission
@user_can_manage_commission
def commissione_cancella_titolo(request, commissione_id, domanda_id,
                                modulo_id, commissione, commissione_user):
    """
        Deve essere chiamato da una dialog con checkbox di conferma
    """

    bando = commissione.bando
    domanda_bando = get_object_or_404(DomandaBando,
                                      pk=domanda_id,
                                      bando=bando)
    dipendente = domanda_bando.dipendente
    mdb = get_object_or_404(ModuloDomandaBando,
                            pk=modulo_id,
                            domanda_bando__dipendente=dipendente)
    if mdb.added_by_user():
        return render(request, 'custom_message.html',
                      {'avviso': ("Impossibile modificare inserimenti creati dal dipendente.")})
    return_url = reverse('gestione_peo:commissione_domanda_manage',
                         args=[commissione.pk, domanda_id])
    return cancella_titolo_from_domanda(request,
                                        bando,
                                        dipendente,
                                        mdb,
                                        return_url,
                                        mark_domanda_as_modified=False,
                                        log=True)
