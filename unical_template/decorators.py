from django.conf import settings
from django.shortcuts import render

def site_not_in_manteinance(func_to_decorate):
    def new_func(*original_args, **original_kwargs):
        request = original_args[0]
        if not settings.MANTEINANCE or request.user.is_staff:
            return func_to_decorate(*original_args, **original_kwargs)
        else:
            return render(request, 'custom_message.html', 
                         {'avviso': ('Questo servizio è in Manutenzione, '
                                     'le attività riprenderanno '
                                     'presto.')})
    return new_func
