from django.conf import settings
from django.http.response import HttpResponseRedirect
from django.shortcuts import render
from .models import Bando

def _get_bando_queryset(bando_id):
    if bando_id.isdigit(): bando_id = int(bando_id)
    if isinstance(bando_id, int):
        bando = Bando.objects.filter(pk=bando_id)
    elif isinstance(bando_id, str):
        bando = Bando.objects.filter(slug=bando_id)
    if not bando:
        raise Http404()
    return bando


# Controlla la tipologia di utente loggato e verifica lo stato del bando
# Pubblicazione/Collaudo
def check_accessibilita_bando(func_to_decorate):
    def new_func(*original_args, **original_kwargs):
        request = original_args[0]
        dipendente = request.user.dipendente_set.filter(matricola=request.user.matricola).first()
        if not dipendente:
            return HttpResponseRedirect(settings.LOGIN_URL)

        bando = _get_bando_queryset(original_kwargs['bando_id']).first()

        if dipendente.utente.is_staff and not (bando.collaudo or bando.pubblicato):
            return render(request, 'custom_message.html', {'avviso': 'Il Bando {} a cui si sta tentando '
                                                                     'di accedere non è pubblicato, '
                                                                     ' nè si trova in collaudo'.format(bando.slug)})
        elif not dipendente.utente.is_staff and not bando.pubblicato:
            return render(request, 'custom_message.html', {'avviso': 'Il Bando {} a cui si sta tentando '
                                                                     'di accedere non è pubblicato'.format(bando.slug)})
        return func_to_decorate(*original_args, **original_kwargs)
    return new_func


# Controlla la tipologia di utente loggato e verifica lo stato del bando
# Finestra temporale (data_inizio e data_fine) e il termine ultimo di presentazione delle domande
def check_termini_domande(func_to_decorate):
    def new_func(*original_args, **original_kwargs):
        request = original_args[0]

        bando = _get_bando_queryset(original_kwargs['bando_id']).first()

        if bando.non_ancora_iniziato():
            return render(request, 'custom_message.html', {'avviso': 'Impossibile accedere '
                                                                     'al Bando {} selezionato'.format(bando.slug)})
        #elif bando.is_scaduto():
        #    return render(request, 'custom_message.html', {'avviso': 'Impossibile apportare modifiche '
        #                                                             'alla domanda relativa a un bando scaduto '
        #                                                             ' (Bando {} scaduto in data {})'.format(bando.slug,bando.data_fine)})

        #elif bando.presentazione_domande_scaduta():
        #    return render(request, 'custom_message.html', {'avviso': 'Impossibile apportare modifiche '
        #                                                             'alla domanda.<br>I termini sono scauduti '
        #                                                             ' in data {}'.format(bando.data_fine_presentazione_domande)})
        return func_to_decorate(*original_args, **original_kwargs)
    return new_func
