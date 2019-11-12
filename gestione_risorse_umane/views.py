import logging

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.shortcuts import render

from gestione_peo.models import *
from gestione_risorse_umane.models import Dipendente, Avviso
from unical_accounts.models import User
from unical_template.decorators import site_not_in_manteinance
from unical_template.breadcrumbs import BreadCrumbs

from .forms import *
from .decorators import matricola_in_csa

# per stampare in produzione usare logger
# _logger = logging.getLogger(__name__)

@site_not_in_manteinance
@login_required
@matricola_in_csa
def dashboard(request):
    """ landing page """
    dipendente = Dipendente.objects.filter(matricola=request.user.matricola).first()
    # creazione dipendente in gestione_risorse_umane se questo non esiste
    if not dipendente:
        dipendente = Dipendente.objects.create(matricola=request.user.matricola,
                                               nome = request.user.first_name,
                                               cognome = request.user.last_name,
                                               utente=request.user)
        dipendente.sync_csa()
    if not dipendente.utente:
        dipendente.utente = request.user
        dipendente.save()

    if dipendente.utente.is_staff:
        bandi = dipendente.idoneita_peo_staff()
    elif dipendente.idoneita_peo_attivata():
        bandi = dipendente.idoneita_peo_attivata()
    else:
        bandi = Bando.objects.none()

    # Escludi i bandi scaduti!
    excluded_pk=[]
    for bando in bandi:
       if not bando.is_in_corso():
           excluded_pk.append(bando.pk)
    bandi = bandi.exclude(pk__in=excluded_pk)

    domande_bando = dipendente.get_domande_progressione()
    for dom in domande_bando:
        for ban in bandi:
            if dom.bando == ban:
                ban.iniziato_dipendente = True

    # dipendente.sync_csa()
    # n = reverse('domande_peo:accetta_condizioni_bando',
                # args=[bandi.first().pk])
    # _logger.error(n)

    d = {
        'dipendente': dipendente,
        'domande_bando': domande_bando,
        'bandi': bandi,
        'MEDIA_URL': settings.MEDIA_URL,
        'avvisi': Avviso.objects.filter(is_active=1),
        }
    return render(request, "dashboard.html", context=d)


@login_required
def upload_carta_identita(request):
    """
        Primo upload o aggiornamento carta identità dipendente
    """
    dipendente = Dipendente.objects.filter(matricola=request.user.matricola).first()

    if request.method == 'POST':
        # print(request.FILES)
        form = CartaIdentitaForm(request.POST, request.FILES)
        if form.is_valid():
            dipendente.carta_identita_front = request.FILES['carta_identita_front']
            dipendente.carta_identita_retro = request.FILES['carta_identita_retro']
            dipendente.save()
            return HttpResponseRedirect('/')
    else:
        form = CartaIdentitaForm()

    page_title = 'Gestione documento di identità'
    d = {
        'page_title': page_title,
        'breadcrumbs': BreadCrumbs(url_list=(('#', page_title),)),
        'form':form,
        'dipendente': dipendente,
        'MEDIA_URL': settings.MEDIA_URL,
        'IMAGE_TYPES': ', '.join([i.split('/')[1] for i in settings.IMG_PERMITTED_UPLOAD_FILETYPE]),
        'IMAGE_MAX_SIZE': '{} MB.'.format(int(settings.IMG_MAX_UPLOAD_SIZE / (1024.)**2)),
        }
    return render(request, 'upload_carta_identita.html', d)
