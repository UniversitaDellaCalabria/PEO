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
from django.urls import path
from wkhtmltopdf.views import PDFTemplateView

from .views import *

app_name="domande_peo"

urlpatterns = [
    path('bando/<str:bando_id>/domanda/aggiungi/<int:descrizione_indicatore_id>/',
         aggiungi_titolo, name='aggiungi_titolo'),

    path('bando/<str:bando_id>/domanda/modifica/<int:modulo_compilato_id>/',
          modifica_titolo, name='modifica_titolo'),

    path('bando/<str:bando_id>/cancella/domanda/<int:domanda_bando_id>/',
          cancella_domanda, name='cancella_domanda'),

    path('bando/<str:bando_id>/domanda/cancella/modulo/<int:modulo_compilato_id>/',
          cancella_titolo, name='cancella_titolo'),

    path('bando/<str:bando_id>/domanda/',
         dashboard_domanda, name='dashboard_domanda'),
         
    path('bando/<str:bando_id>/domanda/aggiungi',
         scelta_titolo_da_aggiungere, name='scelta_titolo_da_aggiungere'),
        
    path('bando/<int:bando_id>/anteprima/<int:descrizione_indicatore_id>/',
         anteprima_modulo_inserimento, name='anteprima_modulo_inserimento'),
        
    path('bando/<int:bando_id>/anteprima-utente/<int:descrizione_indicatore_id>/',
         anteprima_modulo_inserimento_frontend, name='anteprima_modulo_inserimento_frontend'),

    path('bando/<str:bando_id>/vedi/<int:modulo_domanda_bando_id>/',
         vedi_modulo_inserito, name='vedi_modulo_inserito'),
    
    path('bando/<str:bando_id>/accetta-condizioni/',
         accetta_condizioni_bando, name='accetta_condizioni_bando'), 
         
    path('bando/<str:bando_id>/modifica/<int:modulo_compilato_id>/elimina_allegato/<str:allegato>/',
         elimina_allegato, name='elimina_allegato'), 
         
    path('bando/<str:bando_id>/<int:modulo_compilato_id>/download_allegato/<str:allegato>/',
         download_allegato, name='download_allegato'), 
         
    #path('bando/<str:bando_id>/riepilogo_domanda/<int:domanda_bando_id>/',
    #     PDFTemplateView.as_view(template_name='top_notify.html',
    #                             filename='riepilogo.pdf'), 
    #     name='riepilogo_domanda_pdf'),
    
    path('bando/<str:bando_id>/domanda/riepilogo/<int:domanda_bando_id>/',
          riepilogo_domanda, name='riepilogo_domanda'), 

    path('bando/<str:bando_id>/<int:modulo_compilato_id>/download_pdf',
          download_modulo_inserito_pdf, name='download_modulo_inserito_pdf'),

    path('bando/<str:bando_id>/riepilogo_domanda/<int:domanda_bando_id>/download_pdf',
          download_domanda_pdf, name='download_domanda_pdf'),

    path('bando/<str:bando_id>/domanda/<int:domanda_bando_id>/<str:azione>/',
          chiudi_apri_domanda, name='chiudi_apri_domanda'),

]
