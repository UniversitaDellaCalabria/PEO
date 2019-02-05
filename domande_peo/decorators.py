from django.contrib import messages
from django.http import Http404
from django.http.response import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from gestione_peo.models import Bando
from gestione_peo.decorators import _get_bando_queryset

from gestione_risorse_umane.models import Dipendente
from .models import DomandaBando, ModuloDomandaBando


def abilitato_a_partecipare(func_to_decorate):
    def new_func(*original_args, **original_kwargs):
        request = original_args[0]
        dipendente = request.user.dipendente_set.filter(matricola=request.user.matricola).first()
        bando = _get_bando_queryset(original_kwargs['bando_id']).first()
        if not dipendente.carta_identita_front or not dipendente.carta_identita_retro:
            return render(request, 'custom_message.html',
                          {'avviso': ('Per utilizzare i servizi della '
                                     'piattaforma è necessario caricare '
                                     'il documento di identità')})
        elif request.user.is_staff and bando.collaudo:
            return func_to_decorate(*original_args, **original_kwargs)
        elif bando in dipendente.idoneita_peo_attivata():
            return func_to_decorate(*original_args, **original_kwargs)
        else:
            return render(request, 'custom_message.html',
                          {'avviso': ('Spiacenti ma non risulti '
                                      'essere idoneo a partecipare')})
    return new_func


def domanda_modificabile(func_to_decorate):
    """
    REWORK QUI, bisogna normalizzare le variabili per le views domande_peo
    altrimenti N elif per decorare ogni view
    """
    def new_func(*original_args, **original_kwargs):
        request = original_args[0]
        domanda = None

        if original_kwargs.get('modulo_compilato_id'):
            # views.modifica_titolo(request, bando_id, modulo_compilato_id)
            # views.cancella_titolo(request, bando_id, modulo_compilato_id)
            # views.elimina_allegato(request, bando_id, modulo_compilato_id, allegato)
            mdb = ModuloDomandaBando.objects.filter(pk=original_kwargs['modulo_compilato_id']).first()
            if mdb:
                domanda = mdb.domanda_bando
            else:
                raise Http404()
        elif original_kwargs.get('domanda_bando_id'):
            domanda = DomandaBando.objects.get(pk=original_kwargs['domanda_bando_id'])
        elif original_kwargs.get('bando_id'):
            # views.aggiungi_titolo(request, bando_id, descrizione_indicatore_id)
            # views.modifica_titolo(request, bando_id, modulo_compilato_id)
            # views.cancella_titolo(request, bando_id, modulo_compilato_id)
            # views.elimina_allegato(request, bando_id, modulo_compilato_id, allegato)
            # views.cancella_domanda(request, bando_id, domanda_bando_id)
            bando = _get_bando_queryset(original_kwargs['bando_id']).first()
            dipendente = get_object_or_404(Dipendente, matricola=request.user.matricola)
            domanda = DomandaBando.objects.get(bando=bando,
                                               dipendente=dipendente)
        if request.method == 'GET':
            return func_to_decorate(*original_args, **original_kwargs)
        elif request.method == 'POST':
            if domanda.modificabile():
                return func_to_decorate(*original_args, **original_kwargs)
            else:
                messages.error(request, 'Non è possibile modificare una domanda già chiusa.')
                page_url = reverse('domande_peo:dashboard_domanda',
                           args=[domanda.bando.slug])+'#{}'.format(domanda.bando.slug)
                return HttpResponseRedirect(page_url)
    return new_func


def domanda_cancellabile(func_to_decorate):
    """
    Applicandosi solo al metodo 'cancella_domanda',
    il REWORK specificato nel decorator precedente qui non ha senso,
    basta, eventualmente, solo rinominare 'domanda_bando_id'
    """
    def new_func(*original_args, **original_kwargs):
        request = original_args[0]
        domanda = DomandaBando.objects.get(pk=original_kwargs['domanda_bando_id'])
        if not domanda.descr_ind_non_cancellabili():
            return func_to_decorate(*original_args, **original_kwargs)
        else:
            messages.error(request, 'Non è possibile distruggere la domanda.')
            page_url = reverse('domande_peo:dashboard_domanda',
                       args=[domanda.bando.slug])+'#{}'.format(domanda.bando.slug)
            return HttpResponseRedirect(page_url)
    return new_func


def modulo_compilato_cancellabile(func_to_decorate):
    """
    """
    def new_func(*original_args, **original_kwargs):
        request = original_args[0]
        dipendente = get_object_or_404(Dipendente, matricola = request.user.matricola)
        mdb = get_object_or_404(ModuloDomandaBando,
                                pk=original_kwargs['modulo_compilato_id'],
                                domanda_bando__is_active=True,
                                domanda_bando__dipendente=dipendente)
        if mdb.descrizione_indicatore.non_cancellabile:
            messages.error(request, 'Non è possibile eliminare questo modulo.')
            page_url = reverse('domande_peo:dashboard_domanda',
                       args=[mdb.domanda_bando.bando.slug])
            page_url = page_url +'#{}'.format(mdb.domanda_bando.bando.slug)
            return HttpResponseRedirect(page_url)
        else:
            return func_to_decorate(*original_args, **original_kwargs)
    return new_func
