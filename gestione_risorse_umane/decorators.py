from django.conf import settings
from django.shortcuts import render

from csa.models import V_ANAGRAFICA, _get_matricola

def matricola_in_csa(func_to_decorate):
    def new_func(*original_args, **original_kwargs):
        request = original_args[0]
        if not getattr(request.user, 'matricola') or \
        not getattr(request.user, 'first_name') or \
        not getattr(request.user, 'last_name') or \
        not V_ANAGRAFICA.objects.filter(matricola=_get_matricola(request.user.matricola)):
            return render(request, 'utente_non_valido.html')
        return func_to_decorate(*original_args, **original_kwargs)
    return new_func

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
