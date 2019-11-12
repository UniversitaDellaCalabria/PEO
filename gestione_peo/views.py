import json

from django.conf import settings
from django.contrib import auth
from django.contrib.auth.decorators import (login_required,
                                            user_passes_test)
from django.http import Http404
from django.http.response import HttpResponseRedirect
from django.urls import reverse
from django.utils.http import is_safe_url

from django.db.models import Q
from django.shortcuts import render_to_response, get_object_or_404, render
from django.utils import timezone

from .decorators import _get_bando_queryset, check_accessibilita_bando, check_termini_domande
from django_auto_serializer.auto_serializer import ImportableSerializedInstance
from .forms import *
from .models import *

from domande_peo.decorators import abilitato_a_partecipare
from domande_peo.utils import download_file
from gestione_risorse_umane.models import Dipendente
from unical_accounts.models import User
from unical_template.breadcrumbs import BreadCrumbs


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
    breadcrumbs = BreadCrumbs()
    breadcrumbs.add_url((page_url, page_title))

    context = {
        "page_title": page_title,
        "breadcrumbs": breadcrumbs,
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
    breadcrumbs = BreadCrumbs()
    breadcrumbs.add_url((url_bandi_peo,'Bandi PEO'))
    breadcrumbs.add_url((page_url, page_title))
    d = {
         "page_title": page_title,
         "breadcrumbs": breadcrumbs,
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
