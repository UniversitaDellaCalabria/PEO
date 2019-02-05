"""django_peo URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
import logging

from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls import handler404, handler500

from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.urls import include, path, re_path

from unical_template.views import *

# Logging
# logger = logging.getLogger(__name__)
# hdlr = logging.handlers.SysLogHandler( address = '/dev/log',
                                       # facility = logging.handlers.SysLogHandler.LOG_USER )
# logger.addHandler( hdlr )
# formatter = logging.Formatter('%(name)s: %(levelname)s %(message)s')
# hdlr.setFormatter( formatter )
# logger.setLevel( logging.INFO )

# admin labels
admin.site.site_header = 'Amministrazione'
admin.site.pretitle    = 'pretitle in urls.py'
admin.site.site_title  = 'Pannello di amministrazione'

urlpatterns = [
    path('gestione/', admin.site.urls),
    path('logout/', logout_view, name='logout'),
    path('500/', test_500, name='test_500'),
    path('timeout/<seconds>', test_timeout, name='test_timeout'),
]

handler500 = error_500

if settings.DEBUG:
    # STATICS FILE SERVE
    from django.views.static import serve
    urlpatterns.append(
        path('{}/<path>'.format(settings.STATIC_URL[1:-1]),
            serve,
            {'document_root': settings.STATIC_ROOT,
             'show_indexes' : True})
    )
    # MEDIA FILE SERVE
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    # protected download in production environment
    urlpatterns.append(
        # [1:] avoids: (urls.W002) Your URL pattern '/media//<path>' has a route beginning with a '/'
        re_path('{}/(?P<path>[a-zA-Z0-9\_\-\.1\/]+)'.format(settings.MEDIA_URL[1:-1]),
                protected_serve, name='protected_download')
    )
    urlpatterns.append(
        # [1:] avoids: (urls.W002) Your URL pattern '/media//<path>' has a route beginning with a '/'
        re_path('{}{}/(?P<path>[a-zA-Z0-9\_\-\.1\/]+)'.format(settings.HOSTNAME,
                                                              settings.MEDIA_URL[1:-1]),
                protected_serve, name='protected_download')
    )


if 'adminactions' in settings.INSTALLED_APPS:
    from django.contrib.admin import site
    import adminactions.actions as actions
    import adminactions.urls
    urlpatterns += path('adminactions/', include((adminactions.urls, 'adminactions'))),
    actions.add_to_site(site)

if 'advanced_filters' in settings.INSTALLED_APPS:
    import advanced_filters.urls
    urlpatterns += path('advanced_filters/', include((advanced_filters.urls, 'advanced_filters'))),

# Esempio di come includere gli urls delle app solo se queste sono installate
if 'nested_admin' in settings.INSTALLED_APPS:
    import nested_admin.views
    urlpatterns += path('server-data\.js', nested_admin.views.server_data_js,
                        name="nesting_server_data"),

if 'unical_template' in settings.INSTALLED_APPS:
    import unical_template.urls
    urlpatterns += path('template/', include(unical_template.urls, namespace='unical_template')),

if 'gestione_risorse_umane' in settings.INSTALLED_APPS:
    import gestione_risorse_umane.urls
    urlpatterns += path('', include(gestione_risorse_umane.urls, namespace='risorse_umane')),

if 'gestione_peo' in settings.INSTALLED_APPS:
    import gestione_peo.urls
    urlpatterns += path('', include(gestione_peo.urls, namespace='gestione_peo')),

if 'domande_peo' in settings.INSTALLED_APPS:
    import domande_peo.urls
    urlpatterns += path('', include(domande_peo.urls, namespace='domande_peo')),

if 'saml2_sp' in settings.INSTALLED_APPS:
    import saml2_sp.urls
    urlpatterns += path('', include((saml2_sp.urls, 'sp',))),

# PER TROVARE UN BUG che appare solo in produzione con il girotondo di import e urlpatterns
# for i in urlpatterns:
    # _logger.error('\n')
    # _logger.error(i)
    # _logger.error(i.__dict__.get('namespace'))
    # if i.__dict__.get('url_patterns'):
        # for up in i.__dict__.get('url_patterns'):
            # _logger.error(('    ', up))
    # else:
        # _logger.error('... has no url patterns!!!!')
