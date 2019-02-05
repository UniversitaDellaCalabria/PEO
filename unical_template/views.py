import logging
import time

from django.conf import settings
from django.contrib import auth
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.http import (HttpResponseRedirect,
                         HttpResponseForbidden,
                         HttpResponseServerError,
                         HttpResponse)
from django.views.static import serve
from django.shortcuts import render
from django.urls import reverse
from django.utils.http import is_safe_url
from django.shortcuts import render_to_response, get_object_or_404

# Logging
logger = logging.getLogger(__name__)
hdlr = logging.handlers.SysLogHandler( address = '/dev/log',
                                       facility = logging.handlers.SysLogHandler.LOG_USER )
logger.addHandler( hdlr )
formatter = logging.Formatter('%(name)s: %(levelname)s %(message)s')
hdlr.setFormatter( formatter )
logger.setLevel( logging.INFO )

def redirect(request):
    return HttpResponseRedirect('http://www.example.org')

def base_template(request):
    """render the home page"""
    context = {
        "username": '',
        "peer": '',
        "error": "user name e/o password errati"
    }    
    return render(request, "base.html", context=context)

def dashboard_template(request):
    """render the dashboard page"""
    return render(request, "dashboard_peo.html")

def logout_view(request):
    logout(request)
    return HttpResponseRedirect(request.GET.get('next'))

def protected_serve(request, path):
    """
    solo i proprietari degli uploads possono scaricare
    inoltre se è il server stesso a fare una request il download è consentito
    (utile per pdf download via wkhtmltopdf)
    """
    # logger.info('protected download called')
    document_root = settings.MEDIA_ROOT
    # logger.info(document_root)
    # logger.info(path)
    folders = path.split('/')
    
    # logger.info(folders)
    self_request = (request.META.get('REMOTE_ADDR', 0) == \
                    request.META.get('SERVER_ADDR', 1))
    staff_request = request.user.is_staff
    its_owner = False
    if hasattr(request.user, 'matricola'):
        its_owner = request.user.matricola in folders
    
    #logging.info(request.user)
    #logging.info(its_owner)
    
    # check se la matricola dell'utente corrisponde all'utente loggato
    # se REMOTE_ADDRESS == SERVER_ADDR significa che è una richiesta di produzione pdf
    if its_owner or self_request or staff_request:
        #logger.info('{} downloaded "{}"'.format(request.user.matricola, path))
        return serve(request, path, document_root=document_root, show_indexes=False)
    return HttpResponseForbidden()

def test_500(request):
    #return HttpResponseServerError()
    return not_existent_var

def error_500(request):
    return render(request, 'custom_500.html', {})

@login_required
def test_timeout(request, seconds=12):
    time.sleep(int(seconds))
    return HttpResponse('OK,  {} seconds'.format(seconds))
