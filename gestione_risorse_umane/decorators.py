from django.apps import apps
from django.conf import settings
from django.contrib import messages
from django.shortcuts import get_object_or_404, render, redirect
from django.utils.translation import gettext as _

#from csa.models import V_ANAGRAFICA, _get_matricola
from django_form_builder.utils import _successivo_ad_oggi

#def matricola_in_csa(func_to_decorate):
    #def new_func(*original_args, **original_kwargs):
        #request = original_args[0]
        #if not getattr(request.user, 'matricola') or \
        #not getattr(request.user, 'first_name') or \
        #not getattr(request.user, 'last_name') or \
        #not V_ANAGRAFICA.objects.filter(matricola=_get_matricola(request.user.matricola)):
            #return render(request, 'utente_non_valido.html')
        #return func_to_decorate(*original_args, **original_kwargs)
    #return new_func

class is_apps_installed(object):
    """
        This decorator tests if these apps are currently installed
        before execute a class method.

        if not returns False
    """
    def __init__(self, app_names_list):
        # print("INIT ClassBasedDecoratorWithParams")
        if type(app_names_list) != list:
            raise "A list of name must be used as argument. Es: ['app_name1', 'app_name2']"
        self.apps = app_names_list

    def __call__(self, fn, *args, **kwargs):
        # print("CALL ClassBasedDecoratorWithParams")
        def wrapped_func(*args, **kwargs):
            for i in self.apps:
                if i not in settings.INSTALLED_APPS:
                    return False
            # print("Function has been decorated. Congratulations.")
            return fn(*args, **kwargs)
        return wrapped_func

def user_in_commission(func_to_decorate):
    def new_func(*args, **kwargs):
        request = args[0]
        commissione_model = apps.get_model(app_label='gestione_peo',
                                           model_name='CommissioneGiudicatrice')
        commissione = get_object_or_404(commissione_model,
                                        pk=kwargs['commissione_id'],
                                        is_active=True)
        kwargs['commissione'] = commissione
        commissione_users_model = apps.get_model(app_label='gestione_peo',
                                                 model_name='CommissioneGiudicatriceUsers')
        commissione_user = get_object_or_404(commissione_users_model,
                                             user=request.user,
                                             commissione=commissione,
                                             is_active=True)
        kwargs['commissione_user'] = commissione_user
        return func_to_decorate(*args, **kwargs)
    return new_func

# Deve essere seguire sempre @user_can_manage_commission
def user_can_manage_commission(func_to_decorate):
    def new_func(*args, **kwargs):
        commissione = kwargs['commissione']
        commissione_user = kwargs['commissione_user']
        request = args[0]
        termine_presentazione_domande = commissione.bando.data_fine_presentazione_domande
        if _successivo_ad_oggi(termine_presentazione_domande.date()):
            return render(request, 'custom_message.html',
                          {'avviso': _("Non è consentito apportare modifiche alle domande "
                                       "prima della scadenza dei termini: "
                                       "{}".format(termine_presentazione_domande))})
        if not commissione.is_in_corso():
            return render(request, 'custom_message.html',
                          {'avviso': _("Commissione non attiva")})
        if not commissione_user.ha_accettato_clausole():
            return render(request, 'custom_message.html',
                          {'avviso': _("E' necessario accettare le clausole della Commissione")})
        return func_to_decorate(*args, **kwargs)
    return new_func
